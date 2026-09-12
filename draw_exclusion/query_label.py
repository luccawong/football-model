from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from draw_exclusion import MATCH_FAILED, NOT_IN_SOURCE_POOL, SOURCE_SNAPSHOT_MISSING
from draw_exclusion.markets import require_market, scoped_result
from draw_exclusion.indexer import _entry
from draw_exclusion.matcher import SourcePoolMatcher
from draw_exclusion.aliases import AliasRegistry
from draw_exclusion.crawler.snapshot_manager import atomic_json


def _unknown(status: str, **extra) -> dict:
    return {"external_draw_exclusion_label": None, "status": status, **extra}


def _manual_items(root: Path, market: str) -> list[dict]:
    path = root / "manual_labels.json"
    if not path.exists():
        return []
    return [item for item in json.loads(path.read_text(encoding="utf-8")).get("labels", []) if item.get("active", True) and item.get("source_market") == market]


def _manual_result(item: dict) -> dict:
    label = item["label"]
    return {
        "external_draw_exclusion_label": label,
        "status": "MATCHED_EXCLUDED" if label == 1 else "MATCHED_NOT_EXCLUDED",
        "research_match_id": item.get("research_match_id"),
        "titan_match_id": item.get("titan_match_id"),
        "label_origin": item.get("label_origin", "USER_MANUAL"),
        "source": item.get("source_name", "USER_MANUAL"),
        "snapshot_id": item.get("snapshot_id"),
        "snapshot_time": item.get("snapshot_time", item.get("entered_at")),
        "provenance": [item],
    }


def _manual_by_titan(root: Path, titan_match_id: str, market: str) -> dict | None:
    matches = [item for item in _manual_items(root, market) if str(item.get("titan_match_id")) == str(titan_match_id)]
    return _manual_result(matches[-1]) if len(matches) == 1 else None


def _manual_by_fixture(root: Path, date: str, league: str | None, home: str, away: str, market: str) -> dict | None:
    items = _manual_items(root, market)
    if not items:
        return None
    aliases = AliasRegistry(root / "config" if (root / "config").exists() else None)
    home_id, away_id = aliases.team(home).canonical_id, aliases.team(away).canonical_id
    league_id = aliases.competition(league).canonical_id if league else None
    matches = []
    for item in items:
        if item.get("date") != date:
            continue
        item_home = item.get("home_team_canonical_id") or aliases.team(item.get("home_team", "")).canonical_id
        item_away = item.get("away_team_canonical_id") or aliases.team(item.get("away_team", "")).canonical_id
        item_league = item.get("competition_canonical_id") or aliases.competition(item.get("competition", "")).canonical_id
        if item_home == home_id and item_away == away_id and (league_id is None or item_league == league_id):
            matches.append(item)
    return _manual_result(matches[-1]) if len(matches) == 1 else None


def _enqueue_review(root: Path, query: dict, result: dict) -> None:
    path = root / "manual_review_queue.json"
    payload = {"schema_version": "1.0", "items": []}
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    key = json.dumps(query, ensure_ascii=False, sort_keys=True)
    if not any(item.get("query_key") == key for item in payload["items"]):
        payload["items"].append({
            "query_key": key,
            "query": query,
            "reason": result.get("matched_by"),
            "confidence": result.get("confidence"),
            "candidates": result.get("candidates", []),
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "PENDING",
        })
        atomic_json(path, payload)


def query_by_titan(root: Path, titan_match_id: str, *, market: str) -> dict:
    require_market(market)
    index_path = root / "index.json"
    if not index_path.exists():
        return scoped_result(market, _manual_by_titan(root, titan_match_id, market) or
                             _unknown(SOURCE_SNAPSHOT_MISSING, titan_match_id=titan_match_id))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if index.get("schema_version") == "3.0":
        entry = index["by_market"][market]["by_titan_match_id"].get(str(titan_match_id))
    else:
        # A v2 index may already have collapsed conflicting markets. Read its evidence.
        from draw_exclusion.indexer import _select
        candidates = []
        for path in sorted((root / "daily").glob("????-??-??.json")):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if manifest.get("source_status") != "OK":
                continue
            candidates.extend((row, manifest) for row in manifest["matches"]
                              if row["source_market"] == market
                              and str(row.get("titan_match_id")) == str(titan_match_id))
        entry = _select(candidates) if candidates else None
    return scoped_result(market, entry or _manual_by_titan(root, titan_match_id, market) or
                         _unknown(MATCH_FAILED, titan_match_id=titan_match_id,
                                  reason="NO_MARKET_TITAN_CROSSWALK"))


def query_by_fixture(
    root: Path,
    *,
    market: str,
    date: str,
    league: str | None,
    home: str,
    away: str,
    kickoff: str | None,
) -> dict:
    require_market(market)
    paths: list[Path] = []
    index_path = root / "index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        paths = [root / item for item in index.get("by_kickoff_date", {}).get(date, [])]
    direct = root / "daily" / f"{date}.json"
    if direct.exists() and direct not in paths:
        paths.append(direct)
    if not paths:
        return scoped_result(market, _manual_by_fixture(root, date, league, home, away, market) or _unknown(SOURCE_SNAPSHOT_MISSING, date=date))
    manifests = [json.loads(path.read_text(encoding="utf-8")) for path in paths if path.exists()]
    manifests = [item for item in manifests if item.get("source_status") == "OK"]
    if not manifests:
        return scoped_result(market, _manual_by_fixture(root, date, league, home, away, market) or _unknown(SOURCE_SNAPSHOT_MISSING, date=date))
    rows = []
    for manifest in manifests:
        for row in manifest["matches"]:
            if row["source_market"] != market:
                continue
            enriched = dict(row)
            enriched["_entry"] = _entry(row, manifest)
            enriched["_snapshot_time"] = manifest["snapshot"]["snapshot_time_beijing"]
            rows.append(enriched)
    # Different daily pools can repeat a fixture. Match the most recent pool
    # observation within this market, retaining conflicts in that observation.
    newest_dates = {}
    for row in rows:
        key = row["research_match_id"]
        newest_dates[key] = max(newest_dates.get(key, ""), row["_entry"]["date"])
    rows = [row for row in rows if row["_entry"]["date"] == newest_dates[row["research_match_id"]]]
    if kickoff and "T" not in kickoff:
        kickoff = f"{date}T{kickoff}:00+08:00"
    result = SourcePoolMatcher(rows, AliasRegistry(root / "config" if (root / "config").exists() else None)).match(
        market=market,
        date=date, competition=league, home_team=home, away_team=away, kickoff_time=kickoff
    ).to_dict()
    if result["status"] == MATCH_FAILED and not result["review_required"]:
        return scoped_result(market, _manual_by_fixture(root, date, league, home, away, market) or {
            **result, "status": NOT_IN_SOURCE_POOL
        })
    if result.get("review_required"):
        _enqueue_review(root, {
            "market": market, "date": date, "league": league, "home": home, "away": away, "kickoff": kickoff,
        }, result)
    if result.get("research_match_id"):
        matched_rows = [row for row in rows if row["research_match_id"] == result["research_match_id"]]
        newest = max(matched_rows, key=lambda row: row["_snapshot_time"])
        result.update(newest["_entry"])
    return scoped_result(market, result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the external draw-exclusion teacher label.")
    parser.add_argument("--market", required=True, choices=("JC", "BD"))
    parser.add_argument("--match-id", help="Titan match_id")
    parser.add_argument("--date")
    parser.add_argument("--league")
    parser.add_argument("--home")
    parser.add_argument("--away")
    parser.add_argument("--kickoff", help="ISO timestamp or Beijing HH:MM")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    if args.match_id:
        result = query_by_titan(args.root, args.match_id, market=args.market)
    elif args.date and args.home and args.away:
        result = query_by_fixture(
            args.root, market=args.market, date=args.date, league=args.league, home=args.home,
            away=args.away, kickoff=args.kickoff,
        )
    else:
        parser.error("use --match-id, or provide --date --home --away")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
