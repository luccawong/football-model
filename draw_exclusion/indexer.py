from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .crawler.snapshot_manager import atomic_json
from .markets import MARKETS, layer, market_key, scoped_result


def _entry(row: dict, manifest: dict) -> dict:
    return scoped_result(row["source_market"], {
        "research_match_id": row["research_match_id"],
        "market_key": market_key(row["research_match_id"], row["source_market"]),
        "titan_match_id": row.get("titan_match_id"),
        "date": manifest["date"],
        "external_draw_exclusion_label": row["external_draw_exclusion_label"],
        "status": "MATCHED_EXCLUDED" if row["external_draw_exclusion_label"] == 1 else "MATCHED_NOT_EXCLUDED",
        "snapshot_id": row["snapshot_id"],
        "snapshot_time": manifest["snapshot"]["snapshot_time_beijing"],
        "source": manifest["snapshot"].get("source_url"),
        "provenance": row.get("provenance", []),
        "manifest": f"daily/{manifest['date']}.json",
    })


def _select(values: list[tuple[dict, dict]]) -> dict:
    latest = max(values, key=lambda item: item[1]["snapshot"]["snapshot_time_beijing"])
    current = [item for item in values if item[1]["date"] == latest[1]["date"]]
    outcomes = {(r["research_match_id"], r["external_draw_exclusion_label"]) for r, _ in current}
    entry = _entry(*latest)
    if len(outcomes) > 1:
        entry.update(external_draw_exclusion_label=None, status="AMBIGUOUS_MATCH",
                     candidates=[_entry(*item) for item in current])
    return scoped_result(latest[0]["source_market"], entry)


def rebuild_index(root: Path) -> dict:
    """Rebuild derived indexes from old or new manifests without rewriting evidence."""
    manifests = []
    for path in sorted((root / "daily").glob("????-??-??.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("source_status") == "OK":
            manifests.append(payload)
    research, titan = defaultdict(list), defaultdict(list)
    by_kickoff_date = defaultdict(set)
    for manifest in manifests:
        for row in manifest["matches"]:
            key = market_key(row["research_match_id"], row["source_market"])
            research[key].append((row, manifest))
            by_kickoff_date[row["kickoff_time"][:10]].add(f"daily/{manifest['date']}.json")
            if row.get("titan_match_id") is not None:
                titan[(str(row["titan_match_id"]), row["source_market"])].append((row, manifest))
    by_market = {m: {"by_titan_match_id": {}, "by_research_match_id": {}} for m in MARKETS}
    for values in research.values():
        entry = _select(values)
        by_market[entry["market"]]["by_research_match_id"][entry["research_match_id"]] = entry
    for (match_id, market), values in titan.items():
        by_market[market]["by_titan_match_id"][match_id] = _select(values)

    def paired(field: str) -> dict:
        keys = set().union(*(by_market[m][field] for m in MARKETS))
        return {key: {f"{m}_layer": layer(m, by_market[m][field].get(key)) for m in MARKETS}
                for key in sorted(keys)}

    latest_date = max((item["date"] for item in manifests), default=None)
    index = {
        "schema_version": "3.0", "latest_date": latest_date,
        "by_market": by_market,
        "by_market_key": {key: _select(values) for key, values in research.items()},
        "by_titan_match_id": paired("by_titan_match_id"),
        "by_research_match_id": paired("by_research_match_id"),
        "by_kickoff_date": {key: sorted(value) for key, value in sorted(by_kickoff_date.items())},
        "manifests": {item["date"]: f"daily/{item['date']}.json" for item in manifests},
    }
    atomic_json(root / "index.json", index)
    atomic_json(root / "latest.json", {
        "latest_date": latest_date, "manifest": f"daily/{latest_date}.json" if latest_date else None,
    })
    return index
