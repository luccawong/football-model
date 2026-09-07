"""OddsPapi v5 REST client and Betfair Exchange normalizer.

Secrets are read by callers from environment variables and are never logged.
This bridge is pre-match evidence collection only; it never places bets.
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

API_HOST = "https://v5.oddspapi.io/en"
SOCCER_SPORT_ID = 10

class OddsPapiError(RuntimeError):
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

def api_get(path: str, api_key: str, params: Optional[Mapping[str, Any]] = None, attempts: int = 3):
    api_key = (api_key or "").strip()
    if not api_key:
        raise OddsPapiError("OddsPapi API key is missing.")
    query = dict(params or {})
    query["apiKey"] = api_key
    req = Request(API_HOST + path + "?" + urlencode(query, doseq=True), headers={"User-Agent": "gpt-football-exchange-bridge/1.1"})
    for i in range(attempts):
        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8")), {"limit": resp.headers.get("X-RateLimit-Limit"), "remaining": resp.headers.get("X-RateLimit-Remaining"), "reset": resp.headers.get("X-RateLimit-Reset")}
        except HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8")[:500]
            except Exception:
                pass
            if exc.code == 429 and i + 1 < attempts:
                time.sleep(2 ** (i + 1))
                continue
            raise OddsPapiError(f"OddsPapi HTTP {exc.code}: {body}") from None
        except URLError as exc:
            if i + 1 < attempts:
                time.sleep(2 ** i)
                continue
            raise OddsPapiError(f"OddsPapi network error: {exc.reason}") from None
    raise OddsPapiError("OddsPapi request failed.")

def fetch_sports(api_key: str):
    return api_get("/sports", api_key)

def fetch_markets(api_key: str, sport_id: int = SOCCER_SPORT_ID):
    return api_get("/markets", api_key, {"sportId": sport_id})

def fetch_fixtures(api_key: str, *, fixture_ids: Optional[Sequence[str]] = None, sport_id: int = SOCCER_SPORT_ID, start_time_from: Optional[int] = None, start_time_to: Optional[int] = None, status_id: Optional[int] = 0):
    params: Dict[str, Any] = {}
    if fixture_ids:
        params["fixtureIds"] = ",".join(str(x) for x in fixture_ids)
    else:
        params["sportId"] = int(sport_id)
        if start_time_from is not None: params["startTimeFrom"] = int(start_time_from)
        if start_time_to is not None: params["startTimeTo"] = int(start_time_to)
        if status_id is not None: params["statusId"] = int(status_id)
    return api_get("/fixtures", api_key, params)

def fetch_fixture_odds(api_key: str, fixture_id: str, bookmakers: Optional[Sequence[str]] = None):
    params: Dict[str, Any] = {"fixtureId": fixture_id}
    if bookmakers:
        params["bookmakers"] = ",".join(bookmakers)
    return api_get("/fixtures/odds", api_key, params)

def build_1x2_outcome_map(markets: Sequence[Mapping[str, Any]]) -> Dict[int, str]:
    out: Dict[int, str] = {}
    for m in markets:
        if str(m.get("marketType", "")).casefold() != "1x2": continue
        period = str(m.get("period", "")).casefold()
        if period not in {"fulltime", "result", "regular_time", "regular time"}: continue
        if bool(m.get("playerProp", False)): continue
        try: handicap = float(m.get("handicap", 0) or 0)
        except Exception: handicap = 0.0
        if abs(handicap) > 1e-9: continue
        for row in m.get("outcomes", []) or []:
            name = str(row.get("outcomeName", "")).strip().casefold()
            label = {"1":"home", "x":"draw", "draw":"draw", "2":"away"}.get(name)
            if label:
                try: out[int(row["outcomeId"])] = label
                except Exception: pass
    return out

def _participant_names(fixture: Mapping[str, Any]) -> Tuple[str, str]:
    p = fixture.get("participants", {}) or {}
    return str(p.get("participant1Name", "")), str(p.get("participant2Name", ""))

def match_fixture(fixtures: Sequence[Mapping[str, Any]], home_team: str, away_team: str, start_time: Optional[int] = None, tolerance_minutes: int = 180, provider_fixture_id: Optional[str] = None) -> Mapping[str, Any]:
    if provider_fixture_id:
        found = [f for f in fixtures if str(f.get("fixtureId")) == str(provider_fixture_id)]
        if len(found) == 1: return found[0]
        raise OddsPapiError(f"OddsPapi fixtureId {provider_fixture_id!r} was not uniquely found.")
    candidates: List[Tuple[float, float, Mapping[str, Any]]] = []
    for f in fixtures:
        home, away = _participant_names(f)
        hs, aw = _name_score(home_team, home), _name_score(away_team, away)
        if min(hs, aw) < 0.60: continue
        delta = 0.0
        if start_time is not None:
            try: delta = abs(int(f.get("startTime")) - int(start_time)) / 60.0
            except Exception: continue
            if delta > tolerance_minutes: continue
        candidates.append(((hs + aw) / 2.0, -delta, f))
    if not candidates: raise OddsPapiError("No OddsPapi fixture matched the configured teams/kickoff.")
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2]

def _is_betfair_slug(slug: str) -> bool:
    return "betfair" in (slug or "").casefold()

def _best_back(meta: Mapping[str, Any]):
    good = []
    for r in (meta or {}).get("back") or []:
        try: good.append({"price": float(r["price"]), "size": float(r.get("size", 0) or 0)})
        except Exception: continue
    return max(good, key=lambda x: x["price"]) if good else None

def _best_lay(meta: Mapping[str, Any]):
    good = []
    for r in (meta or {}).get("lay") or []:
        try: good.append({"price": float(r["price"]), "size": float(r.get("size", 0) or 0)})
        except Exception: continue
    return min(good, key=lambda x: x["price"]) if good else None

def normalize_fixture_odds(response: Mapping[str, Any], match_id: str, outcome_map: Mapping[int, str], observed_at: Optional[str] = None) -> Dict[str, Any]:
    home, away = _participant_names(response)
    bookmaker_meta = response.get("bookmakers", {}) or {}
    odds_root = response.get("odds", {}) or {}
    betfair_slugs = sorted({str(k) for k in set(bookmaker_meta) | set(odds_root) if _is_betfair_slug(str(k))})
    venues: List[Dict[str, Any]] = []
    for slug in betfair_slugs:
        selections = {"home": {}, "draw": {}, "away": {}}
        entries = list((odds_root.get(slug) or {}).values())
        by_label: Dict[str, List[Mapping[str, Any]]] = {"home": [], "draw": [], "away": []}
        for e in entries:
            try: oid = int(e.get("outcomeId"))
            except Exception: continue
            label = outcome_map.get(oid)
            if not label: continue
            if e.get("active") is False or e.get("marketActive") is False or e.get("mainLine") is False: continue
            by_label[label].append(e)
        for label, rows in by_label.items():
            if not rows: continue
            rows.sort(key=lambda e: int(e.get("changedAt", 0) or 0), reverse=True)
            e = rows[0]; meta = e.get("meta") or {}
            back, lay = _best_back(meta), _best_lay(meta)
            if back is None and e.get("price") is not None:
                try: back = {"price": float(e["price"]), "size": 0.0}
                except Exception: pass
            selections[label] = {"price": e.get("price"), "limit": e.get("limit"), "back": back, "lay": lay, "bookmakerChangedAt": e.get("bookmakerChangedAt"), "changedAt": e.get("changedAt"), "marketId": e.get("marketId"), "outcomeId": e.get("outcomeId"), "raw_meta": meta}
        meta = bookmaker_meta.get(slug) or {}
        venues.append({"bookmaker_slug": slug, "hasOdds": meta.get("hasOdds"), "staleOdds": meta.get("staleOdds"), "suspended": meta.get("suspended"), "updatedAt": meta.get("updatedAt"), "selections": selections})
    selected = venues[0] if venues else None
    return {"schema_version":"exchange-packet-1.1", "bridge_version":"EXCHANGE-BRIDGE-1.1.0", "engine_version":"GPT-EXCHANGE-1.0.0", "provider":"ODDSPAPI", "provider_mode":"BETFAIR_ORDERBOOK", "venue":"Betfair Exchange", "match_id":str(match_id), "provider_fixture_id":response.get("fixtureId"), "sport":response.get("sport"), "tournament":response.get("tournament"), "start_time":response.get("startTime"), "home_team":home, "away_team":away, "observed_at":observed_at or utc_now_iso(), "selected_bookmaker":selected, "all_betfair_bookmakers":venues, "qc":{"fixture_present":bool(response.get("fixtureId")), "betfair_bookmaker_present":bool(venues), "back_ladder_present":bool(selected and any(v.get("back") for v in selected["selections"].values())), "lay_ladder_present":bool(selected and any(v.get("lay") for v in selected["selections"].values())), "stale_odds":bool(selected and selected.get("staleOdds") is True), "total_matched_available":False, "order_book_meta_preserved":True}, "unavailable_fields":["total_matched", "traded_ladder", "traded_volume_velocity"]}
