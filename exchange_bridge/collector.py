"""Collect OddsPapi v4 Betfair Exchange snapshots for configured football targets."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .oddspapi import (
    BETFAIR_BOOKMAKER,
    OddsPapiError,
    SOCCER_SPORT_ID,
    fetch_fixture,
    fetch_fixture_odds,
    fetch_fixtures,
    match_fixture,
    normalize_fixture_odds,
)

ROOT = Path(__file__).resolve().parents[1]
WATCHLIST = ROOT / "config" / "exchange_watchlist.json"
OUT_ROOT = ROOT / "exchange_packets"
# OddsPapi v4 canonical football Full Time Result market (marketId=101).
SOCCER_FT_1X2_OUTCOME_MAP = {101: "home", 102: "draw", 103: "away"}


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _active_target(target: Mapping[str, Any], now: datetime, default_start_hours: float) -> bool:
    if not target.get("enabled", True):
        return False
    kickoff = target.get("commence_time")
    if not kickoff:
        return True
    try:
        ko = _dt(str(kickoff))
    except Exception:
        return True
    start_h = float(target.get("start_hours_before_kickoff", default_start_hours))
    stop_min = float(target.get("stop_minutes_before_kickoff", 0))
    return (ko - timedelta(hours=start_h)) <= now < (ko - timedelta(minutes=stop_min))


def _write_packet(packet: Mapping[str, Any]) -> None:
    folder = OUT_ROOT / str(packet["match_id"])
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "latest.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (folder / "timeline.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(packet, ensure_ascii=False, sort_keys=True) + "\n")


def _secret() -> str:
    # ODDSPAPI_API_KEY is the canonical name; legacy fallback keeps the user's
    # already-configured secret working without exposing or re-entering it.
    return (os.environ.get("ODDSPAPI_API_KEY") or os.environ.get("THE_ODDS_API_KEY") or "").strip()


def main() -> int:
    if not WATCHLIST.exists():
        print("SKIP: exchange watchlist does not exist.")
        return 0
    cfg = json.loads(WATCHLIST.read_text(encoding="utf-8"))
    if not cfg.get("enabled", True):
        print("SKIP: exchange watchlist disabled.")
        return 0

    now = datetime.now(timezone.utc)
    default_start = float(cfg.get("default_start_hours_before_kickoff", 6))
    targets = [t for t in cfg.get("matches", []) if _active_target(t, now, default_start)]
    if not targets:
        print("SKIP: no active OddsPapi v4 exchange targets; no billable API request sent.")
        return 0

    key = _secret()
    if not key:
        print("FAIL: ODDSPAPI_API_KEY/THE_ODDS_API_KEY secret is not available.")
        return 2

    failures = 0
    for target in targets:
        match_id = str(target.get("match_id", "")).strip()
        if not match_id:
            failures += 1
            continue
        tol = int(target.get("kickoff_tolerance_minutes", 180))
        fixture_id = str(target.get("provider_fixture_id") or "").strip() or None
        try:
            if fixture_id:
                fixture, _ = fetch_fixture(key, fixture_id)
                fixtures = [fixture]
            else:
                kickoff = _dt(str(target["commence_time"]))
                fixtures, _ = fetch_fixtures(
                    key,
                    sport_id=SOCCER_SPORT_ID,
                    from_time=_iso(kickoff - timedelta(minutes=tol)),
                    to_time=_iso(kickoff + timedelta(minutes=tol)),
                    status_id=0,
                    bookmaker=BETFAIR_BOOKMAKER,
                )

            fixture = match_fixture(
                fixtures,
                str(target.get("api_home_team") or target.get("home_team") or ""),
                str(target.get("api_away_team") or target.get("away_team") or ""),
                str(target.get("commence_time") or "") or None,
                tol,
                fixture_id,
            )
            fid = str(fixture["fixtureId"])
            odds, rate = fetch_fixture_odds(key, fid, BETFAIR_BOOKMAKER)
            packet = normalize_fixture_odds(
                odds,
                match_id,
                SOCCER_FT_1X2_OUTCOME_MAP,
                bookmaker=BETFAIR_BOOKMAKER,
            )
            packet["rate_limit"] = rate
            packet["target"] = {
                "titan_home_team": target.get("home_team"),
                "titan_away_team": target.get("away_team"),
                "api_home_team": target.get("api_home_team"),
                "api_away_team": target.get("api_away_team"),
            }
            _write_packet(packet)
            selected = packet.get("selected_bookmaker") or {}
            print(
                f"OK match_id={match_id} fixtureId={fid} "
                f"betfair={selected.get('bookmaker_slug')} "
                f"exchangeMeta={packet['qc'].get('exchange_meta_present')}"
            )
        except (OddsPapiError, KeyError, ValueError) as exc:
            print(f"FAIL match_id={match_id}: {exc}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
