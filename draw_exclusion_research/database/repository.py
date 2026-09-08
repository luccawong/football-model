from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.index.match_index_builder import normalize

from draw_exclusion_research.crawler.draw_site_parser import ParsedPage, SiteMatch
from draw_exclusion_research.crawler.snapshot_manager import StoredSnapshot


def connect(database_path: Path, schema_path: Path | None = None) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    schema = schema_path or Path(__file__).with_name("schema.sql")
    connection.executescript(schema.read_text(encoding="utf-8"))
    return connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def insert_snapshot(connection: sqlite3.Connection, snapshot: StoredSnapshot, page: ParsedPage) -> None:
    now = _now()
    with connection:
        connection.execute(
            """INSERT INTO website_snapshots (
                snapshot_id, snapshot_time_utc, snapshot_time_beijing, source_url, http_date,
                page_update_time, http_last_modified, sha256, html_size, html_path,
                content_version, same_hash_as_previous, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot.snapshot_id,
                snapshot.snapshot_time_utc,
                snapshot.snapshot_time_beijing,
                snapshot.source_url,
                snapshot.http_date,
                snapshot.page_reported_update_time,
                snapshot.last_modified,
                snapshot.sha256,
                snapshot.html_size,
                snapshot.html_path,
                snapshot.content_version,
                snapshot.same_hash_as_previous,
                now,
            ),
        )
        for match in page.matches:
            connection.execute(
                """INSERT INTO matches (
                    research_match_id, competition, competition_normalized, home_team,
                    home_team_normalized, away_team, away_team_normalized, kickoff_time,
                    first_source_market, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(research_match_id) DO UPDATE SET updated_at=excluded.updated_at""",
                (
                    match.research_match_id,
                    match.competition,
                    normalize(match.competition),
                    match.home_team,
                    normalize(match.home_team),
                    match.away_team,
                    normalize(match.away_team),
                    match.kickoff_time,
                    match.source_market,
                    now,
                    now,
                ),
            )
            connection.execute(
                """INSERT INTO website_labels (
                    snapshot_id, research_match_id, source_market, website_draw_exclusion_label,
                    site_row_index, site_data_key, match_number, is_single_game
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot.snapshot_id,
                    match.research_match_id,
                    match.source_market,
                    match.website_draw_exclusion_label,
                    match.site_row_index,
                    match.site_data_key,
                    match.match_number,
                    int(match.is_single_game),
                ),
            )
            connection.execute(
                """INSERT INTO site_visible_odds (
                    snapshot_id, research_match_id, source_market, home_1x2, draw_1x2,
                    away_1x2, asian_line, asian_line_raw, home_water, away_water
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot.snapshot_id,
                    match.research_match_id,
                    match.source_market,
                    match.visible_home_1x2,
                    match.visible_draw_1x2,
                    match.visible_away_1x2,
                    match.visible_asian_handicap,
                    match.visible_asian_handicap_raw,
                    match.visible_home_water,
                    match.visible_away_water,
                ),
            )


def compare_and_store_snapshot_diff(connection: sqlite3.Connection, snapshot: StoredSnapshot) -> dict:
    day = snapshot.snapshot_time_beijing[:10]
    previous = connection.execute(
        """SELECT snapshot_id FROM website_snapshots
        WHERE snapshot_id <> ? AND substr(snapshot_time_beijing, 1, 10) = ?
          AND snapshot_time_beijing < ?
        ORDER BY snapshot_time_beijing DESC LIMIT 1""",
        (snapshot.snapshot_id, day, snapshot.snapshot_time_beijing),
    ).fetchone()
    empty = {
        "previous_snapshot_id": None,
        "added": [],
        "deleted": [],
        "label_changed": [],
        "odds_changed": [],
    }
    if previous is None:
        diff = empty
    else:
        previous_id = previous["snapshot_id"]

        def observations(snapshot_id: str) -> dict:
            rows = connection.execute(
                """SELECT wl.research_match_id, wl.source_market, wl.site_data_key,
                          wl.website_draw_exclusion_label, svo.home_1x2, svo.draw_1x2,
                          svo.away_1x2, svo.asian_line, svo.home_water, svo.away_water
                FROM website_labels wl
                JOIN site_visible_odds svo USING (snapshot_id, research_match_id, source_market)
                WHERE wl.snapshot_id=?""",
                (snapshot_id,),
            ).fetchall()
            return {(row["research_match_id"], row["source_market"]): dict(row) for row in rows}

        old = observations(previous_id)
        new = observations(snapshot.snapshot_id)
        old_keys, new_keys = set(old), set(new)
        added = [new[key]["site_data_key"] for key in sorted(new_keys - old_keys)]
        deleted = [old[key]["site_data_key"] for key in sorted(old_keys - new_keys)]
        label_changed = []
        odds_changed = []
        odds_fields = ("home_1x2", "draw_1x2", "away_1x2", "asian_line", "home_water", "away_water")
        for key in sorted(old_keys & new_keys):
            if old[key]["website_draw_exclusion_label"] != new[key]["website_draw_exclusion_label"]:
                label_changed.append(
                    {
                        "site_data_key": new[key]["site_data_key"],
                        "from": old[key]["website_draw_exclusion_label"],
                        "to": new[key]["website_draw_exclusion_label"],
                    }
                )
            changed_fields = [field for field in odds_fields if old[key][field] != new[key][field]]
            if changed_fields:
                odds_changed.append({"site_data_key": new[key]["site_data_key"], "fields": changed_fields})
        diff = {
            "previous_snapshot_id": previous_id,
            "added": added,
            "deleted": deleted,
            "label_changed": label_changed,
            "odds_changed": odds_changed,
        }
    with connection:
        connection.execute(
            """INSERT INTO snapshot_diffs (
                snapshot_id, previous_snapshot_id, added_rows, deleted_rows,
                label_changed_rows, odds_changed_rows, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot.snapshot_id,
                diff["previous_snapshot_id"],
                len(diff["added"]),
                len(diff["deleted"]),
                len(diff["label_changed"]),
                len(diff["odds_changed"]),
                json.dumps(diff, ensure_ascii=False, sort_keys=True),
                _now(),
            ),
        )
    return diff


def insert_resolution(
    connection: sqlite3.Connection,
    snapshot_id: str,
    match: SiteMatch,
    resolution: dict,
) -> None:
    titan_id = resolution.get("match_id")
    with connection:
        connection.execute(
            """INSERT INTO match_resolutions (
                snapshot_id, research_match_id, source_market, status, titan_match_id,
                matched_by, candidate_count, candidates_json, source_batch, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot_id,
                match.research_match_id,
                match.source_market,
                resolution["status"],
                titan_id,
                resolution.get("matched_by"),
                resolution.get("candidate_count", 0),
                json.dumps(resolution.get("candidates", []), ensure_ascii=False, sort_keys=True),
                (resolution.get("resolved_from") or {}).get("batch_file"),
                _now(),
            ),
        )
        if titan_id:
            connection.execute(
                "UPDATE matches SET titan_match_id=?, updated_at=? WHERE research_match_id=?",
                (titan_id, _now(), match.research_match_id),
            )


def insert_external_event(
    connection: sqlite3.Connection,
    research_match_id: str,
    titan_match_id: str,
    market: str,
    event: dict,
    source: str,
) -> bool:
    prices = event.get("decimal_prices") or event.get("prices")
    if not isinstance(prices, list) or any(value is None for value in prices):
        return False
    if market in ("ah", "ou") and event.get("line") is None:
        return False
    company = event.get("company_normalized_name") or event.get("company_raw_name") or "UNKNOWN"
    source_record_id = event.get("record_id")
    key = "|".join(
        str(value)
        for value in (
            research_match_id,
            market,
            company,
            event.get("timestamp"),
            source_record_id,
            event.get("line"),
            prices,
        )
    )
    event_id = "evt_" + hashlib.sha256(key.encode("utf-8")).hexdigest()
    common = (
        event_id,
        research_match_id,
        titan_match_id,
        company,
        event.get("timestamp"),
    )
    tail = (
        event.get("quote_role"),
        source,
        source_record_id,
        json.dumps(event, ensure_ascii=False, sort_keys=True),
        _now(),
    )
    if market == "1x2" and len(prices) == 3:
        sql = """INSERT OR IGNORE INTO external_1x2 (
            event_id, research_match_id, titan_match_id, company, odds_time,
            home, draw, away, quote_role, source, source_record_id, raw_json, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        values = common + tuple(float(value) for value in prices) + tail
    elif market == "ah" and len(prices) == 2:
        sql = """INSERT OR IGNORE INTO external_ah (
            event_id, research_match_id, titan_match_id, company, odds_time,
            line, home_price, away_price, quote_role, source, source_record_id, raw_json, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        values = common + (float(event["line"]),) + tuple(float(value) for value in prices) + tail
    elif market == "ou" and len(prices) == 2:
        sql = """INSERT OR IGNORE INTO external_ou (
            event_id, research_match_id, titan_match_id, company, odds_time,
            line, over_price, under_price, quote_role, source, source_record_id, raw_json, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        values = common + (float(event["line"]),) + tuple(float(value) for value in prices) + tail
    else:
        return False
    with connection:
        cursor = connection.execute(sql, values)
    return cursor.rowcount > 0
