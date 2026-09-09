"""OddsPapi v4 REST client and Betfair Exchange normalizer.

Primary production source for the GPT football Exchange layer.
Secrets are never logged or serialized. Exchange-specific `exchangeMeta` is
preserved raw because its shape may vary by bookmaker/feed version.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

API_HOST = "https://api.oddspapi.io/v4"
SOCCER_SPORT_ID = 10
BETFAIR_BOOKMAKER = "betfair-ex"


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


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def api_get(path: str, api_key: str, params: Optional[Mapping[str, Any]] = None, attempts: int = 3):
    api_key = (api_key or "").strip()
    if not api_key:
        raise OddsPapiError("OddsPapi API key is missing.")
    query = dict(params or {})
    query["apiKey"] = api_key
    req = Request(
        API_HOST + path + "?" + urlencode(query, doseq=True),
        headers={"User-Agent": "gpt-football-exchange-bridge/1.2"},
    )
    for i in range(attempts):
        try:
            with urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                rate = {
                    "limit": resp.headers.get("X-RateLimit-Limit"),
                    "remaining": resp.headers.get("X-RateLimit-Remaining"),
                    "reset": resp.headers.get("X-RateLimit-Reset"),
                }
                return payload, rate
        except HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8")[:500]
            except Exception:
                pass
            if exc.code == 429 and i + 1 < attempts:
                time.sleep(2 ** (i + 1))
                continue
            raise OddsPapiError(f"OddsPapi v4 HTTP {exc.code}: {body}") from None
        except URLError as exc:
            if i + 1 < attempts:
                time.sleep(2 ** i)
                continue
            raise OddsPapiError(f"OddsPapi v4 network error: {exc.reason}") from None
    raise OddsPapiError("OddsPapi v4 request failed.")


def fetch_account(api_key: str):
    """Unmetered v4 credential/subscription check."""
    return api_get("/account", api_key)


def fetch_markets(api_key: str):
    return api_get("/markets", api_key, {"language": "en"})


def fetch_fixture(api_key: str, fixture_id: str):
    return api_get("/fixture", api_key, {"fixtureId": fixture_id, "language": "en"})


def fetch_fixtures(
    api_key: str,
    *,
    sport_id: int = SOCCER_SPORT_ID,
    from_time: str,
    to_time: str,
    status_id: int = 0,
    bookmaker: str = BETFAIR_BOOKMAKER,
):
    params = {
        "sportId": int(sport_id),
        "from": from_time,
        "to": to_time,
        "statusId": int(status_id),
        "hasOdds": "true",
        "bookmakers": bookmaker,
        "language": "en",
    }
    return api_get("/fixtures", api_key, params)


def fetch_fixture_odds(api_key: str, fixture_id: str, bookmaker: str = BETFAIR_BOOKMAKER):
    return api_get(
        "/odds",
        api_key,
        {
            "fixtureId": fixture_id,
            "bookmakers": bookmaker,
            "oddsFormat": "decimal",
            "language": "en",
            "verbosity": 3,
        },
    )


def build_1x2_outcome_map(markets: Sequence[Mapping[str, Any]]) -> Dict[int, str]:
    out: Dict[int, str] = {}
    for market in markets:
        try:
            if int(market.get("sportId", -1)) != SOCCER_SPORT_ID:
                continue
        except Exception:
            continue
        if str(market.get("marketType", "")).casefold() != "1x2":
            continue
        if str(market.get("period", "")).casefold() != "fulltime":
            continue
        if bool(market.get("playerProp", False)):
            continue
        try:
            if abs(float(market.get("handicap", 0) or 0)) > 1e-9:
                continue
        except Exception:
            continue
        for row in market.get("outcomes", []) or []:
            label = {"1": "home", "x": "draw", "draw": "draw", "2": "away"}.get(
                str(row.get("outcomeName", "")).strip().casefold()
            )
            if label:
                try:
                    out[int(row["outcomeId"])] = label
                except Exception:
                    pass
    return out


def _participant_names(fixture: Mapping[str, Any]) -> Tuple[str, str]:
    return str(fixture.get("participant1Name", "")), str(fixture.get("participant2Name", ""))


def match_fixture(
    fixtures: Sequence[Mapping[str, Any]],
    home_team: str,
    away_team: str,
    commence_time: Optional[str] = None,
    tolerance_minutes: int = 180,
    provider_fixture_id: Optional[str] = None,
) -> Mapping[str, Any]:
    if provider_fixture_id:
        found = [f for f in fixtures if str(f.get("fixtureId")) == str(provider_fixture_id)]
        if len(found) == 1:
            return found[0]
        raise OddsPapiError(f"OddsPapi fixtureId {provider_fixture_id!r} was not uniquely found.")
    target_dt = _parse_iso(commence_time) if commence_time else None
    candidates: List[Tuple[float, float, Mapping[str, Any]]] = []
    for fixture in fixtures:
        home, away = _participant_names(fixture)
        hs, aw = _name_score(home_team, home), _name_score(away_team, away)
        if min(hs, aw) < 0.60:
            continue
        delta = 0.0
        if target_dt is not None:
            try:
                delta = abs((_parse_iso(str(fixture.get("startTime"))) - target_dt).total_seconds()) / 60.0
            except Exception:
                continue
            if delta > tolerance_minutes:
                continue
        candidates.append(((hs + aw) / 2.0, -delta, fixture))
    if not candidates:
        raise OddsPapiError("No OddsPapi v4 fixture matched the configured teams/kickoff.")
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2]


def _player_zero(outcome: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    players = outcome.get("players", {}) or {}
    if "0" in players:
        return players["0"]
    if 0 in players:
        return players[0]
    if len(players) == 1:
        return next(iter(players.values()))
    return None


def normalize_fixture_odds(
    response: Mapping[str, Any],
    match_id: str,
    outcome_map: Mapping[int, str],
    observed_at: Optional[str] = None,
    bookmaker: str = BETFAIR_BOOKMAKER,
) -> Dict[str, Any]:
    home, away = _participant_names(response)
    root = response.get("bookmakerOdds", {}) or {}
    book = root.get(bookmaker) or {}
    selections: Dict[str, Dict[str, Any]] = {"home": {}, "draw": {}, "away": {}}

    for market_id, market in (book.get("markets", {}) or {}).items():
        if market.get("marketActive") is False:
            continue
        for outcome_id_raw, outcome in (market.get("outcomes", {}) or {}).items():
            try:
                outcome_id = int(outcome_id_raw)
            except Exception:
                continue
            label = outcome_map.get(outcome_id)
            if not label:
                continue
            row = _player_zero(outcome)
            if not row or row.get("active") is False or row.get("mainLine") is False:
                continue
            selections[label] = {
                "price": row.get("price"),
                "limit": row.get("limit"),
                "bookmakerChangedAt": row.get("bookmakerChangedAt"),
                "changedAt": row.get("changedAt"),
                "exchangeMeta": row.get("exchangeMeta"),
                "bookmakerOutcomeId": row.get("bookmakerOutcomeId"),
                "marketId": int(market_id) if str(market_id).isdigit() else market_id,
                "outcomeId": outcome_id,
            }

    exchange_meta_present = any(v.get("exchangeMeta") is not None for v in selections.values())
    selected = {
        "bookmaker_slug": bookmaker,
        "bookmakerIsActive": book.get("bookmakerIsActive"),
        "bookmakerFixtureId": book.get("bookmakerFixtureId"),
        "fixturePath": book.get("fixturePath"),
        "suspended": book.get("suspended"),
        "selections": selections,
    } if book else None

    return {
        "schema_version": "exchange-packet-1.2",
        "bridge_version": "EXCHANGE-BRIDGE-1.2.0",
        "engine_version": "GPT-EXCHANGE-1.0.0",
        "provider": "ODDSPAPI_V4",
        "provider_mode": "BETFAIR_EXCHANGE_META",
        "venue": "Betfair Exchange",
        "match_id": str(match_id),
        "provider_fixture_id": response.get("fixtureId"),
        "sport_id": response.get("sportId"),
        "tournament_id": response.get("tournamentId"),
        "status_id": response.get("statusId"),
        "start_time": response.get("startTime"),
        "home_team": home,
        "away_team": away,
        "observed_at": observed_at or utc_now_iso(),
        "selected_bookmaker": selected,
        "qc": {
            "fixture_present": bool(response.get("fixtureId")),
            "betfair_bookmaker_present": bool(book),
            "market_not_suspended": bool(book) and book.get("suspended") is not True,
            "home_price_present": selections["home"].get("price") is not None,
            "draw_price_present": selections["draw"].get("price") is not None,
            "away_price_present": selections["away"].get("price") is not None,
            "exchange_meta_present": exchange_meta_present,
            "exchange_meta_preserved_raw": True,
            "total_matched_available": False,
        },
        "unavailable_fields": [
            "total_matched",
            "traded_ladder",
            "traded_volume_velocity",
            "guaranteed_multi_level_back_lay_depth",
        ],
    }
