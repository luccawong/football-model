"""Minimal The Odds API client and deterministic Betfair Exchange normalizer.

Uses only Python stdlib. Never logs or serializes the API key.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import time
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

API_HOST = "https://api.the-odds-api.com"
BETFAIR_KEYS = ("betfair_ex_uk", "betfair_ex_eu", "betfair_ex_au")
PROVIDER_MARKETS = ("h2h", "h2h_lay")


class OddsApiError(RuntimeError):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _norm_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    stop = {"fc", "cf", "afc", "sc", "ac", "calcio", "football", "club"}
    return " ".join(t for t in value.split() if t and t not in stop)


def _name_score(a: str, b: str) -> float:
    na, nb = _norm_name(a), _norm_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    sa, sb = set(na.split()), set(nb.split())
    jaccard = len(sa & sb) / max(1, len(sa | sb))
    contains = 0.92 if (na in nb or nb in na) else 0.0
    return max(jaccard, contains)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def match_event(events: Sequence[Mapping[str, Any]], home_team: str, away_team: str,
                commence_time: Optional[str] = None, tolerance_minutes: int = 180,
                provider_event_id: Optional[str] = None) -> Mapping[str, Any]:
    if provider_event_id:
        found = [e for e in events if str(e.get("id")) == str(provider_event_id)]
        if len(found) == 1:
            return found[0]
        raise OddsApiError(f"Provider event id {provider_event_id!r} was not uniquely found.")
    target_dt = _parse_iso(commence_time) if commence_time else None
    candidates: List[Tuple[float, float, Mapping[str, Any]]] = []
    for event in events:
        hs = _name_score(home_team, str(event.get("home_team", "")))
        aw = _name_score(away_team, str(event.get("away_team", "")))
        if min(hs, aw) < 0.60:
            continue
        score = (hs + aw) / 2.0
        delta = 0.0
        if target_dt is not None:
            try:
                edt = _parse_iso(str(event["commence_time"]))
            except Exception:
                continue
            delta = abs((edt - target_dt).total_seconds()) / 60.0
            if delta > tolerance_minutes:
                continue
        candidates.append((score, -delta, event))
    if not candidates:
        raise OddsApiError("No event matched the configured teams/kickoff.")
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2]


def _quota_headers(headers: Mapping[str, str]) -> Dict[str, Optional[int]]:
    out: Dict[str, Optional[int]] = {}
    for src, dst in (("x-requests-remaining", "remaining"), ("x-requests-used", "used"), ("x-requests-last", "last_cost")):
        raw = headers.get(src)
        try:
            out[dst] = int(raw) if raw is not None else None
        except (TypeError, ValueError):
            out[dst] = None
    return out


def api_get(path: str, api_key: str, params: Optional[Mapping[str, Any]] = None, attempts: int = 3):
    if not api_key:
        raise OddsApiError("THE_ODDS_API_KEY is missing.")
    query = dict(params or {})
    query["apiKey"] = api_key
    req = Request(API_HOST + path + "?" + urlencode(query, doseq=True), headers={"User-Agent": "gpt-football-exchange-bridge/1.0"})
    for i in range(attempts):
        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8")), _quota_headers(resp.headers)
        except HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8")[:500]
            except Exception:
                pass
            if exc.code == 429 and i + 1 < attempts:
                time.sleep(2 ** (i + 1))
                continue
            raise OddsApiError(f"The Odds API HTTP {exc.code}: {body}") from None
        except URLError as exc:
            if i + 1 < attempts:
                time.sleep(2 ** i)
                continue
            raise OddsApiError(f"The Odds API network error: {exc.reason}") from None
    raise OddsApiError("The Odds API request failed.")


def fetch_sports(api_key: str):
    return api_get("/v4/sports/", api_key)


def fetch_exchange_odds(api_key: str, sport_key: str, bookmaker_keys: Sequence[str] = BETFAIR_KEYS):
    params = {"bookmakers": ",".join(bookmaker_keys), "markets": ",".join(PROVIDER_MARKETS),
              "oddsFormat": "decimal", "includeBetLimits": "true"}
    return api_get(f"/v4/sports/{sport_key}/odds", api_key, params)


def _market_outcomes(bookmaker: Mapping[str, Any], key: str):
    for market in bookmaker.get("markets", []) or []:
        if market.get("key") == key:
            return {str(o.get("name")): o for o in market.get("outcomes", []) or []}, market.get("last_update")
    return {}, None


def _selection_label(name: str, home: str, away: str) -> Optional[str]:
    if _norm_name(name) == "draw":
        return "draw"
    if _name_score(name, home) >= 0.60:
        return "home"
    if _name_score(name, away) >= 0.60:
        return "away"
    return None


def normalize_event(event: Mapping[str, Any], match_id: str,
                    preferred_bookmakers: Sequence[str] = BETFAIR_KEYS,
                    observed_at: Optional[str] = None, quota: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    home, away = str(event.get("home_team", "")), str(event.get("away_team", ""))
    rows = []
    for bookmaker in event.get("bookmakers", []) or []:
        key = str(bookmaker.get("key", ""))
        if key not in preferred_bookmakers:
            continue
        backs, bu = _market_outcomes(bookmaker, "h2h")
        lays, lu = _market_outcomes(bookmaker, "h2h_lay")
        selections = {"home": {}, "draw": {}, "away": {}}
        for n, o in backs.items():
            label = _selection_label(n, home, away)
            if label:
                selections[label]["back"] = {"price": o.get("price"), "bet_limit": o.get("bet_limit"), "name": n}
        for n, o in lays.items():
            label = _selection_label(n, home, away)
            if label:
                selections[label]["lay"] = {"price": o.get("price"), "bet_limit": o.get("bet_limit"), "name": n}
        rows.append({"bookmaker_key": key, "bookmaker_title": bookmaker.get("title"),
                     "bookmaker_last_update": bookmaker.get("last_update"), "h2h_last_update": bu,
                     "h2h_lay_last_update": lu, "selections": selections})
    priority = {k: i for i, k in enumerate(preferred_bookmakers)}
    rows.sort(key=lambda r: priority.get(r["bookmaker_key"], 999))
    selected = rows[0] if rows else None
    return {"schema_version": "exchange-packet-1.0", "bridge_version": "EXCHANGE-BRIDGE-1.0.0",
            "engine_version": "GPT-EXCHANGE-1.0.0", "provider": "THE_ODDS_API",
            "provider_mode": "EXCHANGE_LITE", "venue": "Betfair Exchange", "match_id": str(match_id),
            "provider_event_id": event.get("id"), "sport_key": event.get("sport_key"),
            "sport_title": event.get("sport_title"), "commence_time": event.get("commence_time"),
            "home_team": home, "away_team": away, "observed_at": observed_at or utc_now_iso(),
            "selected_bookmaker": selected, "all_exchange_bookmakers": rows, "quota": dict(quota or {}),
            "unavailable_fields": ["full_order_book_depth", "order_book_imbalance_multi_level", "total_matched", "traded_ladder", "traded_volume_velocity"],
            "qc": {"provider_event_present": True, "exchange_bookmaker_present": bool(rows),
                   "back_market_present": bool(selected and any("back" in x for x in selected["selections"].values())),
                   "lay_market_present": bool(selected and any("lay" in x for x in selected["selections"].values())),
                   "deep_order_book_available": False, "total_matched_available": False,
                   "bet_limit_is_not_matched_volume": True}}
