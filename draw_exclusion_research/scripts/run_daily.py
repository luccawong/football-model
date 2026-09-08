from __future__ import annotations

import argparse
import json
from pathlib import Path

from draw_exclusion_research.crawler.draw_site_collector import collect
from draw_exclusion_research.crawler.draw_site_parser import parse_page
from draw_exclusion_research.crawler.snapshot_manager import store_snapshot
from draw_exclusion_research.database.repository import (
    compare_and_store_snapshot_diff,
    connect,
    insert_resolution,
    insert_snapshot,
)
from draw_exclusion_research.integration.titan_adapter import TitanAdapter
from draw_exclusion_research.reports.daily import render_daily_report, write_daily_report


def run(football_model_root: Path, config_path: Path | None = None) -> dict:
    project_root = football_model_root / "draw_exclusion_research"
    config_path = config_path or project_root / "config" / "settings.json"
    settings = json.loads(config_path.read_text(encoding="utf-8"))
    http_snapshot = collect(settings["source_url"], settings["http_timeout_seconds"])
    html = http_snapshot.decode_html()
    page = parse_page(html)
    stored = store_snapshot(project_root, http_snapshot, page.page_reported_update_time)
    database_path = project_root / settings["database_path"]
    connection = connect(database_path)
    try:
        insert_snapshot(connection, stored, page)
        snapshot_diff = compare_and_store_snapshot_diff(connection, stored)
        titan = TitanAdapter(football_model_root)
        timeline_counts = {"1x2": 0, "ah": 0, "ou": 0}
        resolution_counts: dict[str, int] = {}
        for match in page.matches:
            resolution = titan.resolve(match)
            insert_resolution(connection, stored.snapshot_id, match, resolution)
            resolution_counts[resolution["status"]] = resolution_counts.get(resolution["status"], 0) + 1
            inserted = titan.ingest_timeline(connection, match, resolution)
            for market, count in inserted.items():
                timeline_counts[market] += count
        report_text = render_daily_report(connection, stored, page)
        report_path = write_daily_report(project_root, stored, report_text)
    finally:
        connection.close()
    return {
        "snapshot_id": stored.snapshot_id,
        "sha256": stored.sha256,
        "content_version": stored.content_version,
        "html_path": stored.html_path,
        "database_path": database_path.relative_to(football_model_root).as_posix(),
        "report_path": report_path.relative_to(football_model_root).as_posix(),
        "website_rows": len(page.matches),
        "website_excluded": sum(match.website_draw_exclusion_label for match in page.matches),
        "resolution_counts": resolution_counts,
        "inserted_timeline_events": timeline_counts,
        "snapshot_diff": {
            "previous_snapshot_id": snapshot_diff["previous_snapshot_id"],
            "added": len(snapshot_diff["added"]),
            "deleted": len(snapshot_diff["deleted"]),
            "label_changed": len(snapshot_diff["label_changed"]),
            "odds_changed": len(snapshot_diff["odds_changed"]),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze the draw-site report and align it to validated Titan data.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve(), args.config), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
