from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from draw_exclusion_research.database.repository import connect as connect_base


def connect(path: Path) -> sqlite3.Connection:
    connection = connect_base(path)
    connection.executescript(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
    existing = {row[1] for row in connection.execute("PRAGMA table_info(match_crosswalk)")}
    migrations = {
        "source_match_id": "TEXT NOT NULL DEFAULT ''",
        "competition": "TEXT NOT NULL DEFAULT ''",
        "home_team": "TEXT NOT NULL DEFAULT ''",
        "away_team": "TEXT NOT NULL DEFAULT ''",
        "kickoff_time": "TEXT NOT NULL DEFAULT ''",
    }
    for column, declaration in migrations.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE match_crosswalk ADD COLUMN {column} {declaration}")
    return connection


def upsert_crosswalk(connection: sqlite3.Connection, snapshot_id: str, row: dict, resolution: dict) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    confidence = 1.0 if resolution.get("status") == "resolved" else None
    with connection:
        connection.execute(
            """INSERT INTO matches (
                research_match_id, competition, competition_normalized, home_team,
                home_team_normalized, away_team, away_team_normalized, kickoff_time,
                first_source_market, titan_match_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(research_match_id) DO UPDATE SET
                titan_match_id=COALESCE(excluded.titan_match_id, matches.titan_match_id),
                updated_at=excluded.updated_at""",
            (
                row["research_match_id"], row["competition"]["raw_name"], row["competition"]["canonical_id"],
                row["home_team"]["raw_name"], row["home_team"]["canonical_id"],
                row["away_team"]["raw_name"], row["away_team"]["canonical_id"], row["kickoff_time"],
                row["source_market"], resolution.get("match_id"), now, now,
            ),
        )
        connection.execute(
            """INSERT OR REPLACE INTO match_crosswalk (
                research_match_id, titan_match_id, source_match_id, source_market,
                competition, home_team, away_team, kickoff_time, resolution_status,
                matched_by, confidence, source_snapshot_id, provenance_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["research_match_id"], resolution.get("match_id"), row["source_data_key"], row["source_market"],
                row["competition"]["raw_name"], row["home_team"]["raw_name"],
                row["away_team"]["raw_name"], row["kickoff_time"],
                resolution.get("status", "unavailable"), resolution.get("matched_by"), confidence,
                snapshot_id, json.dumps(resolution, ensure_ascii=False, sort_keys=True), now,
            ),
        )


def upsert_evaluation(connection: sqlite3.Connection, snapshot_time: str, row: dict) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connection:
        connection.execute(
            """INSERT OR REPLACE INTO research_evaluation (
                research_match_id, titan_match_id, competition, home_team, away_team,
                kickoff_time, source_market, external_draw_exclusion_label,
                external_label_snapshot_time, label_origin, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row["research_match_id"], row.get("titan_match_id"), row["competition"]["raw_name"],
                row["home_team"]["raw_name"], row["away_team"]["raw_name"], row["kickoff_time"],
                row["source_market"], row["external_draw_exclusion_label"], snapshot_time,
                row["label_origin"], now,
            ),
        )


def store_formal_diff(connection: sqlite3.Connection, snapshot_id: str, diff: dict) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connection:
        connection.execute(
            """INSERT OR REPLACE INTO formal_snapshot_diffs (
                snapshot_id, previous_snapshot_id, added_rows, deleted_rows,
                label_changed_rows, odds_changed_rows, time_changed_rows, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot_id, diff.get("previous_snapshot_id"), len(diff.get("added", [])),
                len(diff.get("deleted", [])), len(diff.get("label_changed", [])),
                len(diff.get("odds_changed", [])), len(diff.get("time_changed", [])),
                json.dumps(diff, ensure_ascii=False, sort_keys=True), now,
            ),
        )
