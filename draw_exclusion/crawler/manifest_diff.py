from __future__ import annotations

import json
from pathlib import Path


def compare_with_promoted_manifest(root: Path, current: dict) -> dict:
    path = root / "daily" / f"{current['date']}.json"
    empty = {
        "previous_snapshot_id": None,
        "added": [],
        "deleted": [],
        "label_changed": [],
        "odds_changed": [],
        "time_changed": [],
    }
    if not path.exists():
        return empty
    previous = json.loads(path.read_text(encoding="utf-8"))
    old = {(row["source_market"], row["source_data_key"]): row for row in previous["matches"]}
    new = {(row["source_market"], row["source_data_key"]): row for row in current["matches"]}
    old_keys, new_keys = set(old), set(new)
    result = {
        "previous_snapshot_id": previous["snapshot"]["snapshot_id"],
        "added": [new[key]["source_data_key"] for key in sorted(new_keys - old_keys)],
        "deleted": [old[key]["source_data_key"] for key in sorted(old_keys - new_keys)],
        "label_changed": [],
        "odds_changed": [],
        "time_changed": [],
    }
    for key in sorted(old_keys & new_keys):
        before, after = old[key], new[key]
        if before["external_draw_exclusion_label"] != after["external_draw_exclusion_label"]:
            result["label_changed"].append({
                "source_data_key": after["source_data_key"],
                "from": before["external_draw_exclusion_label"],
                "to": after["external_draw_exclusion_label"],
            })
        changed_odds = [
            field for field in after["visible_odds"]
            if before.get("visible_odds", {}).get(field) != after["visible_odds"].get(field)
        ]
        if changed_odds:
            result["odds_changed"].append({"source_data_key": after["source_data_key"], "fields": changed_odds})
        if before["kickoff_time"] != after["kickoff_time"]:
            result["time_changed"].append({
                "source_data_key": after["source_data_key"],
                "from": before["kickoff_time"],
                "to": after["kickoff_time"],
            })
    return result

