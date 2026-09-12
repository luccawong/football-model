from __future__ import annotations

from collections import Counter
from pathlib import Path


def qc_summary(manifest: dict) -> dict:
    rows = manifest["matches"]
    markets = {}
    for market in ("JC", "BD"):
        selected = [row for row in rows if row["source_market"] == market]
        excluded = sum(row["external_draw_exclusion_label"] == 1 for row in selected)
        not_excluded = sum(row["external_draw_exclusion_label"] == 0 for row in selected)
        markets[market] = {"total": len(selected), "excluded": excluded, "not_excluded": not_excluded}
    titan = Counter(row["titan_resolution"]["status"] for row in rows)
    duplicate_keys = Counter((row["research_match_id"], row["source_market"]) for row in rows)
    conflicts = list(manifest.get("forensic_conflicts", []))
    by_research: dict[str, set[int]] = {}
    for row in rows:
        by_research.setdefault((row["research_match_id"], row["source_market"]), set()).add(row["external_draw_exclusion_label"])
    for research_id, labels in by_research.items():
        if len(labels) > 1:
            conflicts.append({"research_match_id": research_id[0], "source_market": research_id[1], "labels": sorted(labels)})
    unknown = sum(row["external_draw_exclusion_label"] is None for row in rows)
    missing_identity = sum(
        not row["competition"]["raw_name"] or not row["home_team"]["raw_name"]
        or not row["away_team"]["raw_name"] or not row["kickoff_time"]
        for row in rows
    )
    unregistered_teams = sum(
        not row["home_team"]["alias_registered"] or not row["away_team"]["alias_registered"] for row in rows
    )
    return {
        "source_status": manifest["source_status"],
        "row_count": len(rows),
        "markets": markets,
        "titan_matched": titan.get("resolved", 0),
        "titan_unmatched": len(rows) - titan.get("resolved", 0),
        "fuzzy_matches": 0,
        "duplicates": sum(count - 1 for count in duplicate_keys.values() if count > 1),
        "unknown": unknown,
        "missing_identity": missing_identity,
        "unregistered_team_pairs": unregistered_teams,
        "conflicts": conflicts,
        "invariants_ok": (
            all(item["excluded"] + item["not_excluded"] == item["total"] for item in markets.values())
            and sum(item["total"] for item in markets.values()) == len(rows)
            and unknown == 0 and missing_identity == 0 and not conflicts
        ),
    }


def render_qc(manifest: dict, summary: dict) -> str:
    jc, bd = summary["markets"]["JC"], summary["markets"]["BD"]
    diff = manifest.get("snapshot_diff") or {}
    return f"""# External Draw Exclusion QC — {manifest['date']}

- Source status: `{summary['source_status']}`
- Snapshot: `{manifest['snapshot']['snapshot_id']}`
- SHA-256: `{manifest['snapshot']['sha256']}`
- Page update: `{manifest['snapshot'].get('page_reported_update_time')}`
- Manual screenshot present: `{str(manifest['snapshot'].get('manual_screenshot_present', False)).lower()}`

## Coverage

| Pool | Total | EXCLUDED | NOT_EXCLUDED |
|---|---:|---:|---:|
| 竞彩 (JC) | {jc['total']} | {jc['excluded']} | {jc['not_excluded']} |
| 北单 (BD) | {bd['total']} | {bd['excluded']} | {bd['not_excluded']} |

## Matching and integrity

- Titan ID matched: {summary['titan_matched']}
- Titan unmatched: {summary['titan_unmatched']}
- Fuzzy auto-matches: {summary['fuzzy_matches']}
- Duplicate market rows: {summary['duplicates']}
- UNKNOWN rows inside a valid source pool: {summary['unknown']}
- Rows with unregistered team aliases: {summary['unregistered_team_pairs']}
- Forensic/label conflicts: {len(summary['conflicts'])}
- Invariants: `{'PASS' if summary['invariants_ok'] else 'FAIL'}`

## Same-day snapshot diff

- Added: {len(diff.get('added', []))}
- Deleted: {len(diff.get('deleted', []))}
- Label changed: {len(diff.get('label_changed', []))}
- Odds changed: {len(diff.get('odds_changed', []))}
- Kickoff time changed: {len(diff.get('time_changed', []))}

`0` is emitted only for rows present in this verified pool. A missing match or missing snapshot remains `NULL / UNKNOWN`.
"""


def write_qc(root: Path, manifest: dict, summary: dict) -> Path:
    path = root / "reports" / "daily" / f"{manifest['date']}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_qc(manifest, summary), encoding="utf-8")
    return path
