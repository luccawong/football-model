"""Collect one Exchange Lite snapshot for configured football watchlist targets."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import json, os
from pathlib import Path
from typing import Any, Dict, List, Mapping
from .the_odds_api import BETFAIR_KEYS, OddsApiError, fetch_exchange_odds, match_event, normalize_event, utc_now_iso

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

def main() -> int:
    if not WATCHLIST.exists(): print("SKIP: exchange watchlist does not exist."); return 0
    cfg = json.loads(WATCHLIST.read_text(encoding="utf-8"))
    if not cfg.get("enabled", True): print("SKIP: exchange watchlist disabled."); return 0
    now = datetime.now(timezone.utc)
    default_start = float(cfg.get("default_start_hours_before_kickoff", 6))
    targets = [t for t in cfg.get("matches", []) if _active_target(t, now, default_start)]
    if not targets: print("SKIP: no active exchange targets; no odds API credits used."); return 0
    key = os.environ.get("THE_ODDS_API_KEY", "")
    if not key: print("FAIL: THE_ODDS_API_KEY secret is not available."); return 2
    by_sport: Dict[str, List[Mapping[str, Any]]] = {}
    for target in targets:
        sport = str(target.get("sport_key", "")).strip()
        if not sport: print(f"SKIP match_id={target.get('match_id')}: sport_key missing."); continue
        by_sport.setdefault(sport, []).append(target)
    failures = 0
    for sport_key, sport_targets in by_sport.items():
        try:
            events, quota = fetch_exchange_odds(key, sport_key, bookmaker_keys=tuple(cfg.get("bookmaker_keys", BETFAIR_KEYS)))
        except OddsApiError as exc:
            print(f"FAIL sport={sport_key}: {exc}"); failures += len(sport_targets); continue
        print(f"FETCH sport={sport_key}: events={len(events)} quota_remaining={quota.get('remaining')} cost={quota.get('last_cost')}")
        for target in sport_targets:
            match_id = str(target.get("match_id", "")).strip()
            if not match_id: failures += 1; continue
            try:
                event = match_event(events, str(target.get("api_home_team") or target.get("home_team") or ""), str(target.get("api_away_team") or target.get("away_team") or ""), target.get("commence_time"), int(target.get("kickoff_tolerance_minutes", 180)), target.get("provider_event_id"))
                packet = normalize_event(event, match_id, preferred_bookmakers=tuple(cfg.get("bookmaker_keys", BETFAIR_KEYS)), observed_at=utc_now_iso(), quota=quota)
                packet["target"] = {"titan_home_team": target.get("home_team"), "titan_away_team": target.get("away_team"), "api_home_team": target.get("api_home_team"), "api_away_team": target.get("api_away_team")}
                _write_packet(packet)
                print(f"OK match_id={match_id} provider_event_id={packet.get('provider_event_id')} bookmaker={((packet.get('selected_bookmaker') or {}).get('bookmaker_key'))}")
            except OddsApiError as exc:
                print(f"FAIL match_id={match_id}: {exc}"); failures += 1
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
