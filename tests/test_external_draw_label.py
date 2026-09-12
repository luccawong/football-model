import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from draw_exclusion import (
    AMBIGUOUS_MATCH,
    MATCHED_NOT_EXCLUDED,
    MATCH_FAILED,
    NOT_IN_SOURCE_POOL,
    SOURCE_SNAPSHOT_MISSING,
)
from draw_exclusion.aliases import AliasRegistry
from draw_exclusion.crawler.fetch_draw_site import HttpSnapshot
from draw_exclusion.crawler.snapshot_manager import store_snapshot
from draw_exclusion.database.repository import connect, upsert_crosswalk
from draw_exclusion.indexer import rebuild_index
from draw_exclusion.matcher import SourcePoolMatcher
from draw_exclusion.query_label import query_by_fixture, query_by_titan


def row(research_id="r1", label=0, home="曼城", away="阿森纳", kickoff="2026-09-09T20:00:00+08:00"):
    aliases = AliasRegistry()
    home_name, away_name = aliases.team(home), aliases.team(away)
    competition = aliases.competition("英超")
    return {
        "research_match_id": research_id,
        "titan_match_id": None,
        "source_market": "JC",
        "competition": {"raw_name": "英超", "canonical_id": competition.canonical_id},
        "home_team": {"raw_name": home, "canonical_id": home_name.canonical_id},
        "away_team": {"raw_name": away, "canonical_id": away_name.canonical_id},
        "kickoff_time": kickoff,
        "external_draw_exclusion_label": label,
        "snapshot_id": "s1",
        "source_data_key": "JC|1",
    }


def manifest(rows, date="2026-09-09", status="OK"):
    return {
        "schema_version": "2.0",
        "date": date,
        "source_status": status,
        "snapshot": {"snapshot_id": "s1", "snapshot_time_beijing": f"{date}T17:00:00+08:00"},
        "matches": rows,
    }


class ExternalLabelLayerTests(unittest.TestCase):
    def test_team_aliases_share_canonical_id(self):
        aliases = AliasRegistry()
        self.assertEqual(aliases.team("曼城").canonical_id, aliases.team("Manchester City").canonical_id)

    def test_competition_aliases_share_canonical_id(self):
        aliases = AliasRegistry()
        self.assertEqual(aliases.competition("英超").canonical_id, aliases.competition("EPL").canonical_id)

    def test_zero_requires_actual_source_pool_row(self):
        result = SourcePoolMatcher([row(label=0)]).match(
            market="JC",
            date="2026-09-09", competition="EPL", home_team="Manchester City", away_team="Arsenal"
        )
        self.assertEqual(result.status, MATCHED_NOT_EXCLUDED)
        self.assertEqual(result.external_draw_exclusion_label, 0)

    def test_missing_date_is_unknown_not_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            result = query_by_fixture(
                Path(directory), market="JC", date="2026-09-08", league="英超", home="曼城", away="阿森纳", kickoff=None
            )
        self.assertEqual(result["status"], SOURCE_SNAPSHOT_MISSING)
        self.assertIsNone(result["external_draw_exclusion_label"])

    def test_not_in_source_pool_is_unknown_not_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "daily").mkdir()
            (root / "daily" / "2026-09-09.json").write_text(
                json.dumps(manifest([row()])), encoding="utf-8"
            )
            result = query_by_fixture(
                root, market="JC", date="2026-09-09", league="英超", home="切尔西", away="利物浦", kickoff=None
            )
        self.assertEqual(result["status"], NOT_IN_SOURCE_POOL)
        self.assertIsNone(result["external_draw_exclusion_label"])

    def test_fuzzy_is_review_only_and_never_binary(self):
        result = SourcePoolMatcher([row(home="Manchester City", away="Arsenal")]).match(
            market="JC",
            date="2026-09-09", home_team="Manchester Ctiy", away_team="Arsena1"
        )
        self.assertEqual(result.status, MATCH_FAILED)
        self.assertIsNone(result.external_draw_exclusion_label)
        self.assertTrue(result.review_required)

    def test_conflicting_duplicate_is_ambiguous(self):
        result = SourcePoolMatcher([row("r1", 0), row("r2", 1)]).match(
            market="JC",
            date="2026-09-09", home_team="曼城", away_team="阿森纳"
        )
        self.assertEqual(result.status, AMBIGUOUS_MATCH)
        self.assertIsNone(result.external_draw_exclusion_label)

    def test_beijing_date_boundary_and_immutable_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = HttpSnapshot("https://example.test", datetime(2026, 9, 8, 16, 30, tzinfo=timezone.utc), b"one", None, None, "text/html", 200)
            second = HttpSnapshot("https://example.test", datetime(2026, 9, 8, 16, 31, tzinfo=timezone.utc), b"two", None, None, "text/html", 200)
            a = store_snapshot(root, first, "2026-09-09T00:20:00+08:00")
            b = store_snapshot(root, second, "2026-09-09T00:20:00+08:00")
            self.assertTrue(a.snapshot_time_beijing.startswith("2026-09-09"))
            self.assertEqual((a.content_version, b.content_version), (1, 2))
            self.assertNotEqual(a.html_path, b.html_path)

    def test_titan_crosswalk_and_fast_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            connection = connect(root / "draw.sqlite")
            try:
                connection.execute(
                    """INSERT INTO website_snapshots (
                    snapshot_id,snapshot_time_utc,snapshot_time_beijing,source_url,http_date,page_update_time,
                    http_last_modified,sha256,html_size,html_path,content_version,same_hash_as_previous,created_at
                    ) VALUES ('s1','2026-09-09T09:00:00+00:00','2026-09-09T17:00:00+08:00','x',NULL,NULL,NULL,'h',1,'raw/x',1,NULL,'now')"""
                )
                item = row()
                item.update({
                    "source_research_match_id": "source-r1",
                    "match_number": "周三001",
                    "competition": {"raw_name": "英超", "canonical_id": "premier_league"},
                    "home_team": {"raw_name": "曼城", "canonical_id": "manchester_city"},
                    "away_team": {"raw_name": "阿森纳", "canonical_id": "arsenal"},
                })
                upsert_crosswalk(connection, "s1", item, {"status": "resolved", "match_id": "3049507", "matched_by": "exact"})
                found = connection.execute("SELECT titan_match_id FROM match_crosswalk").fetchone()[0]
                self.assertEqual(found, "3049507")
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            finally:
                connection.close()

            daily = root / "daily"
            daily.mkdir()
            indexed = row()
            indexed["titan_match_id"] = "3049507"
            (daily / "2026-09-09.json").write_text(json.dumps(manifest([indexed])), encoding="utf-8")
            rebuild_index(root)
            result = query_by_titan(root, "3049507", market="JC")
            self.assertEqual(result["external_draw_exclusion_label"], 0)
            self.assertEqual(result["status"], MATCHED_NOT_EXCLUDED)


if __name__ == "__main__":
    unittest.main()
