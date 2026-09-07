"""Collect OddsPapi Betfair Exchange snapshots for configured football targets."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .oddspapi import (
    OddsPapiError, SOCCER_SPORT_ID, build_1x2_outcome_map, fetch_fixture_odds,
    fetch_fixtures, fetch_markets, match_fixture, normalize_fixture_odds,
)

ROOT = Path(__file__).resolve().parents[1]
WATCHLIST = ROOT / "config" / "exchange_watchlist.json"
OUT_ROOT = ROOT / "exchange_packets"

def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

def _active_target(target: Mapping[str, Any], now: datetime, default_start_hours: float) -> bool:
    if not target.get("enabled", True): return False
    kickoff = target.get("commence_time")
    if not kickoff: return True
    try: ko = _dt(str(kickoff))
    except Exception: return True
    start_h = float(target.get("start_hours_before_kickoff", default_start_hours))
    stop_min = float(target.get("stop_minutes_before_kickoff", 0))
    return (ko - timedelta(hours=start_h)) <= now < (ko - timedelta(minutes=stop_min))

def _write_packet(packet: Mapping[str, Any]) -> None:
    folder = OUT_ROOT / str(packet["match_id"])
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "latest.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (folder / "timeline.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(packet, ensure_ascii=False, sort_keys=True) + "\n")

def _secret() -> str:
    return (os.environ.get("ODDSPAPI_API_KEY") or os.environ.get("THE_ODDS_API_KEY") or "").strip()

def main() -> int:
    if not WATCHLIST.exists(): print("SKIP: exchange watchlist does not exist."); return 0
    cfg = json.loads(WATCHLIST.read_text(encoding="utf-8"))
    if not cfg.get("enabled", True): print("SKIP: exchange watchlist disabled."); return 0
    now = datetime.now(timezone.utc)
    default_start = float(cfg.get("default_start_hours_before_kickoff", 6))
    targets = [t for t in cfg.get("matches", []) if _active_target(t, now, default_start)]
    if not targets: print("SKIP: no active OddsPapi exchange targets; no odds request sent."); return 0
    key = _secret()
    if not key: print("FAIL: ODDSPAPI_API_KEY/THE_ODDS_API_KEY secret is not available."); return 2
    try:
        markets, _ = fetch_markets(key, SOCCER_SPORT_ID)
        outcome_map = build_1x2_outcome_map(markets)
    except OddsPapiError as exc:
        print(f"FAIL: cannot load soccer market map: {exc}"); return 1
    if not outcome_map:
        print("FAIL: OddsPapi soccer 1X2 outcome map is empty."); return 1
    failures = 0
    for target in targets:
        match_id = str(target.get("match_id", "")).strip()
        if not match_id: failures += 1; continue
        tol = int(target.get("kickoff_tolerance_minutes", 180))
        fixture_id = str(target.get("provider_fixture_id") or "").strip() or None
        try:
            if fixture_id:
                fixtures, _ = fetch_fixtures(key, fixture_ids=[fixture_id])
            else:
                kickoff = _dt(str(target["commence_time"])); center = int(kickoff.timestamp())
                fixtures, _ = fetch_fixtures(key, sport_id=SOCCER_SPORT_ID, start_time_from=center - tol*60, start_time_to=center + tol*60, status_id=0)
            fixture = match_fixture(fixtures, str(target.get("api_home_team") or target.get("home_team") or ""), str(target.get("api_away_team") or target.get("away_team") or ""), int(_dt(str(target["commence_time"])).timestamp()) if target.get("commence_time") else None, tol, fixture_id)
            fid = str(fixture["fixtureId"])
            odds, rate = fetch_fixture_odds(key, fid)
            packet = normalize_fixture_odds(odds, match_id, outcome_map)
            packet["rate_limit"] = rate
            packet["target"] = {"titan_home_team": target.get("home_team"), "titan_away_team": target.get("away_team"), "api_home_team": target.get("api_home_team"), "api_away_team": target.get("api_away_team")}
            _write_packet(packet)
            selected = packet.get("selected_bookmaker") or {}
            print(f"OK match_id={match_id} fixtureId={fid} betfair={selected.get('bookmaker_slug')} stale={selected.get('staleOdds')}")
        except (OddsPapiError, KeyError, ValueError) as exc:
            print(f"FAIL match_id={match_id}: {exc}"); failures += 1
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
