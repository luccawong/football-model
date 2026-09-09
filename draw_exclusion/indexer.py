from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .crawler.snapshot_manager import atomic_json


def _entry(row: dict, manifest: dict) -> dict:
    return {
        "research_match_id": row["research_match_id"],
        "titan_match_id": row.get("titan_match_id"),
        "date": manifest["date"],
        "external_draw_exclusion_label": row["external_draw_exclusion_label"],
        "status": "MATCHED_EXCLUDED" if row["external_draw_exclusion_label"] == 1 else "MATCHED_NOT_EXCLUDED",
        "source_market": row["source_market"],
        "snapshot_id": row["snapshot_id"],
        "snapshot_time": manifest["snapshot"]["snapshot_time_beijing"],
        "manifest": f"daily/{manifest['date']}.json",
    }


def rebuild_index(root: Path) -> dict:
    manifests = []
    for path in sorted((root / "daily").glob("????-??-??.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("source_status") == "OK":
            manifests.append(payload)
    by_research_groups: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    by_titan_groups: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    by_kickoff_date: dict[str, set[str]] = defaultdict(set)
    for manifest in manifests:
        for row in manifest["matches"]:
            by_research_groups[row["research_match_id"]].append((row, manifest))
            by_kickoff_date[row["kickoff_time"][:10]].add(f"daily/{manifest['date']}.json")
            if row.get("titan_match_id") is not None:
                by_titan_groups[str(row["titan_match_id"])].append((row, manifest))

    def collapse(groups: dict[str, list[tuple[dict, dict]]]) -> dict:
        output = {}
        for key, values in groups.items():
            latest = max(values, key=lambda item: item[1]["snapshot"]["snapshot_time_beijing"])
            labels = {item[0]["external_draw_exclusion_label"] for item in values if item[1]["date"] == latest[1]["date"]}
            if len(labels) > 1:
                output[key] = {
                    "external_draw_exclusion_label": None,
                    "status": "AMBIGUOUS_MATCH",
                    "candidates": [item[0]["research_match_id"] for item in values],
                }
            else:
                output[key] = _entry(*latest)
        return output

    latest_date = max((item["date"] for item in manifests), default=None)
    index = {
        "schema_version": "2.0",
        "latest_date": latest_date,
        "by_titan_match_id": collapse(by_titan_groups),
        "by_research_match_id": collapse(by_research_groups),
        "by_kickoff_date": {key: sorted(value) for key, value in sorted(by_kickoff_date.items())},
        "manifests": {item["date"]: f"daily/{item['date']}.json" for item in manifests},
    }
    atomic_json(root / "index.json", index)
    atomic_json(root / "latest.json", {
        "latest_date": latest_date,
        "manifest": f"daily/{latest_date}.json" if latest_date else None,
    })
    return index
