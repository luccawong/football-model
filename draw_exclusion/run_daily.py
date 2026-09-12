from __future__ import annotations

import argparse
import json
from pathlib import Path

from draw_exclusion_research.database.repository import (
    compare_and_store_snapshot_diff,
    insert_resolution,
    insert_snapshot,
)
from draw_exclusion_research.integration.titan_adapter import TitanAdapter

from draw_exclusion.crawler.build_daily_manifest import build_manifest, write_manifest
from draw_exclusion.crawler.fetch_draw_site import collect
from draw_exclusion.crawler.manifest_diff import compare_with_promoted_manifest
from draw_exclusion.crawler.parse_draw_site import parse_page
from draw_exclusion.crawler.qc import qc_summary, write_qc
from draw_exclusion.crawler.snapshot_manager import store_snapshot
from draw_exclusion.database.repository import connect, store_formal_diff, upsert_crosswalk, upsert_evaluation
from draw_exclusion.indexer import rebuild_index


def run(football_model_root: Path, config_path: Path | None = None) -> dict:
    root = football_model_root / "draw_exclusion"
    settings_path = config_path or root / "config" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    response = collect(settings["source_url"], settings["http_timeout_seconds"])
    page = parse_page(response.decode_html())
    snapshot = store_snapshot(root, response, page.page_reported_update_time)
    capture_date = snapshot.snapshot_time_beijing[:10]
    source_date = (page.page_reported_update_time or "")[:10]
    source_status = "OK" if source_date and source_date == capture_date else "SITE_NOT_UPDATED"

    connection = connect(root / "database" / "draw_exclusion.sqlite")
    try:
        insert_snapshot(connection, snapshot, page)
        diff = compare_and_store_snapshot_diff(connection, snapshot)
        diff.setdefault("time_changed", [])
        titan = TitanAdapter(football_model_root)
        resolutions: dict[tuple[str, str], dict] = {}
        for match in page.matches:
            resolution = titan.resolve(match)
            resolutions[(match.research_match_id, match.source_market)] = resolution
            insert_resolution(connection, snapshot.snapshot_id, match, resolution)
        manifest = build_manifest(root, page, snapshot, resolutions, diff, source_status)
        manifest["snapshot_diff"] = compare_with_promoted_manifest(root, manifest)
        store_formal_diff(connection, snapshot.snapshot_id, manifest["snapshot_diff"])
        for row in manifest["matches"]:
            resolution = resolutions[(row["source_research_match_id"], row["source_market"])]
            upsert_crosswalk(connection, snapshot.snapshot_id, row, resolution)
            upsert_evaluation(connection, snapshot.snapshot_time_beijing, row)
        daily_exists = (root / "daily" / f"{manifest['date']}.json").exists()
        promote = source_status == "OK" and (not daily_exists or snapshot.same_hash_as_previous is not True)
        daily_path, version_path = write_manifest(root, manifest, promote=promote)
        summary = qc_summary(manifest)
        report_path = root / "reports" / "daily" / f"{manifest['date']}.md"
        if promote or not report_path.exists():
            report_path = write_qc(root, manifest, summary)
        index_path = root / "index.json"
        needs_index_upgrade = not index_path.exists() or json.loads(
            index_path.read_text(encoding="utf-8")
        ).get("schema_version") != "3.0"
        if promote or needs_index_upgrade:
            rebuild_index(root)
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
    finally:
        connection.close()

    return {
        "source_status": source_status,
        "source_date": source_date or None,
        "capture_date_beijing": capture_date,
        "snapshot_id": snapshot.snapshot_id,
        "sha256": snapshot.sha256,
        "content_version": snapshot.content_version,
        "same_hash_as_previous": snapshot.same_hash_as_previous,
        "raw_html": snapshot.html_path,
        "daily_manifest": daily_path.relative_to(football_model_root).as_posix() if promote else None,
        "promoted": promote,
        "version_manifest": version_path.relative_to(football_model_root).as_posix(),
        "qc_report": report_path.relative_to(football_model_root).as_posix(),
        "qc": summary,
        "foreign_key_violations": len(foreign_keys),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the formal external draw-exclusion label snapshot.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    result = run(args.root.resolve(), args.config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["source_status"] != "OK" or not result["qc"]["invariants_ok"] or result["foreign_key_violations"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
