import json
import shutil
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from tests.test_external_draw_label import row, manifest
from tests.test_draw_exclusion import fixture_html
from draw_exclusion.crawler.build_daily_manifest import build_manifest
from draw_exclusion.crawler.fetch_draw_site import HttpSnapshot
from draw_exclusion.crawler.parse_draw_site import parse_page
from draw_exclusion.crawler.snapshot_manager import store_snapshot
from draw_exclusion.crawler.qc import qc_summary
from draw_exclusion.database.repository import connect, upsert_crosswalk, upsert_evaluation
from draw_exclusion_research.database.repository import insert_snapshot
from draw_exclusion.indexer import rebuild_index
from draw_exclusion.matcher import SourcePoolMatcher
from draw_exclusion.query_label import query_by_fixture, query_by_titan
from draw_exclusion.markets import model_1_reference
from draw_exclusion.statistics import market_statistics
from gpt.model_1_packet_bridge import build_feature_packet


class MarketIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "daily").mkdir()

    def write_rows(self, jc=None, bd=None):
        rows = []
        for market, label in (("JC", jc), ("BD", bd)):
            if label is not None:
                item = row(label=label)
                item.update(source_market=market, titan_match_id="3049507",
                            provenance=[{"origin": market}], snapshot_id=f"s-{market}")
                rows.append(item)
        data = manifest(rows)
        data["snapshot"]["source_url"] = "https://example.test"
        (self.root / "daily/2026-09-09.json").write_text(json.dumps(data), encoding="utf-8")
        return rebuild_index(self.root)

    def fixture_query(self, market):
        return query_by_fixture(self.root, market=market, date="2026-09-09",
                                league="EPL", home="Manchester City", away="Arsenal", kickoff=None)

    def test_jc_one_bd_zero_remain_independent(self):
        index = self.write_rows(1, 0)
        self.assertEqual(set(index["by_market_key"]), {"r1|JC", "r1|BD"})
        paired = index["by_titan_match_id"]["3049507"]
        self.assertEqual(paired["JC_layer"]["jc_draw_exclusion_label"], 1)
        self.assertEqual(paired["BD_layer"]["bd_draw_exclusion_label"], 0)
        self.assertNotIn("external_draw_exclusion_label", paired)
        for market, expected in (("JC", 1), ("BD", 0)):
            for result in (self.fixture_query(market),
                           query_by_titan(self.root, "3049507", market=market)):
                self.assertEqual(result["label"], expected)
                self.assertNotEqual(result["status"], "AMBIGUOUS_MATCH")
                self.assertEqual(result["snapshot_id"], f"s-{market}")
                self.assertEqual(result["provenance"], [{"origin": market}])

    def test_jc_zero_bd_one(self):
        self.write_rows(0, 1)
        self.assertEqual(self.fixture_query("JC")["label"], 0)
        self.assertEqual(self.fixture_query("BD")["label"], 1)
        self.assertEqual(query_by_titan(self.root, "3049507", market="JC")["label"], 0)
        self.assertEqual(query_by_titan(self.root, "3049507", market="BD")["label"], 1)

    def test_only_jc(self):
        self.write_rows(1, None)
        self.assertEqual(self.fixture_query("JC")["label"], 1)
        self.assertIsNone(self.fixture_query("BD")["label"])
        self.assertEqual(self.fixture_query("BD")["status"], "NOT_IN_SOURCE_POOL")

    def test_only_bd(self):
        self.write_rows(None, 1)
        self.assertEqual(self.fixture_query("BD")["label"], 1)
        self.assertIsNone(self.fixture_query("JC")["label"])
        self.assertIsNone(query_by_titan(self.root, "3049507", market="JC")["label"])

    def test_explicit_market_required_and_invalid_rejected(self):
        with self.assertRaises(TypeError):
            query_by_titan(self.root, "3049507")
        with self.assertRaises(ValueError):
            query_by_titan(self.root, "3049507", market="ALL")
        with self.assertRaises(TypeError):
            SourcePoolMatcher([]).match(date="2026-09-09", home_team="A", away_team="B")

    def test_v2_collapsed_index_recovered_from_manifest_without_mutation(self):
        self.write_rows(1, 0)
        legacy = {"schema_version": "2.0", "by_titan_match_id": {
            "3049507": {"external_draw_exclusion_label": None, "status": "AMBIGUOUS_MATCH"}}}
        path = self.root / "index.json"
        path.write_text(json.dumps(legacy), encoding="utf-8")
        before = path.read_bytes()
        self.assertEqual(query_by_titan(self.root, "3049507", market="JC")["label"], 1)
        self.assertEqual(query_by_titan(self.root, "3049507", market="BD")["label"], 0)
        self.assertEqual(path.read_bytes(), before)

    def test_same_market_conflict_remains_ambiguous(self):
        self.write_rows(1, 0)
        path = self.root / "daily/2026-09-09.json"
        data = json.loads(path.read_text())
        conflicting = dict(data["matches"][0], external_draw_exclusion_label=0)
        data["matches"].append(conflicting)
        path.write_text(json.dumps(data))
        rebuild_index(self.root)
        self.assertEqual(query_by_titan(self.root, "3049507", market="JC")["status"], "AMBIGUOUS_MATCH")
        self.assertEqual(self.fixture_query("JC")["status"], "AMBIGUOUS_MATCH")
        self.assertEqual(self.fixture_query("BD")["label"], 0)

    def test_manual_market_cannot_leak_and_unspecified_market_is_ignored(self):
        self.write_rows(None, None)
        path = self.root / "manual_labels.json"
        path.write_text(json.dumps({"labels": [
            {"titan_match_id": "3049507", "label": 1, "source_market": "BD"},
            {"titan_match_id": "3049507", "label": 0}]}))
        self.assertEqual(query_by_titan(self.root, "3049507", market="BD")["label"], 1)
        self.assertIsNone(query_by_titan(self.root, "3049507", market="JC")["label"])

    def test_model_1_four_combinations_and_missing_jc(self):
        for jc, bd, signal, counter, risk in (
            (1, 1, "STRONG_EXCLUDE", False, False),
            (1, 0, "EXCLUDE", True, False),
            (0, 1, "NO_EXCLUSION_SIGNAL", False, True),
            (0, 0, "NO_EXCLUSION_SIGNAL", False, False),
            (None, 1, "UNKNOWN", False, True),
        ):
            with self.subTest(jc=jc, bd=bd):
                self.write_rows(jc, bd)
                packet = build_feature_packet(match_id="3049507", module_records={},
                                              stage_status={}, external_draw_root=self.root)
                result = packet["external_draw_teacher"]
                self.assertEqual(result["teacher_reference_signal"], signal)
                self.assertEqual(result["bd_counterevidence"], counter)
                self.assertEqual(result["bd_risk_hint"], risk)

    def test_manifest_database_qc_and_statistics(self):
        source = Path(__file__).resolve().parents[1] / "draw_exclusion"
        shutil.copytree(source / "config", self.root / "config")
        for name, content in (("manual_labels.json", {"labels": []}), ("forensic_evidence.json", {"items": []})):
            (self.root / name).write_text(json.dumps(content))
        parsed = parse_page(fixture_html())
        jc = parsed.matches[0]
        bd = replace(jc, source_market="BD", website_draw_exclusion_label=0, site_data_key="BD|same")
        page = replace(parsed, matches=(jc, bd))
        response = HttpSnapshot("https://example.test", datetime(2026, 9, 8, 9, tzinfo=timezone.utc),
                                b"evidence", None, None, "text/html", 200)
        snapshot = store_snapshot(self.root, response, page.page_reported_update_time)
        data = build_manifest(self.root, page, snapshot, {}, {})
        self.assertEqual(data["matches"][0]["research_match_id"], data["matches"][1]["research_match_id"])
        self.assertNotEqual(data["matches"][0]["market_key"], data["matches"][1]["market_key"])
        self.assertEqual(data["matches"][0]["JC_layer"]["jc_draw_exclusion_label"], 1)
        self.assertEqual(data["matches"][0]["BD_layer"]["bd_draw_exclusion_label"], 0)
        self.assertTrue(qc_summary(data)["invariants_ok"])
        connection = connect(self.root / "test.sqlite")
        try:
            insert_snapshot(connection, snapshot, page)
            for item in data["matches"]:
                upsert_crosswalk(connection, snapshot.snapshot_id, item,
                                 {"status": "resolved", "match_id": "3049507"})
                upsert_evaluation(connection, snapshot.snapshot_time_beijing, item)
            connection.execute("UPDATE research_evaluation SET final_is_draw=1, our_draw_exclusion_class='KEEP_DRAW'")
            connection.commit()
            # Re-observation must not erase student decisions or outcomes.
            upsert_evaluation(connection, snapshot.snapshot_time_beijing, data["matches"][0])
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM match_crosswalk").fetchone()[0], 2)
            self.assertEqual(connection.execute("SELECT jc_draw_exclusion_label FROM jc_layer").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT bd_draw_exclusion_label FROM bd_layer").fetchone()[0], 0)
            stats = market_statistics(connection)
            self.assertEqual(stats["JC"]["failures"], 1)
            self.assertEqual(stats["JC_EXCLUDE_BD_NOT_EXCLUDED"]["failure_types"]["ACTUAL_DRAW"], 1)
            self.assertIsNone(stats["BD"]["hit_rate"])
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(connection.execute("SELECT our_draw_exclusion_class FROM research_evaluation").fetchone()[0], "KEEP_DRAW")
        finally:
            connection.close()

    def test_statistics_deduplicates_excludes_post_kickoff_and_scores_bd_lead(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("""CREATE TABLE research_evaluation (
            research_match_id TEXT, source_market TEXT, external_label_snapshot_time TEXT,
            kickoff_time TEXT, external_draw_exclusion_label INTEGER, final_is_draw INTEGER)""")
        try:
            for market, label in (("JC", 0), ("BD", 1)):
                for stamp in ("17:00", "18:00"):
                    connection.execute("INSERT INTO research_evaluation VALUES (?,?,?,?,?,?)",
                                       ("a", market, f"2026-09-09T{stamp}:00+08:00",
                                        "2026-09-09T20:00:00+08:00", label, 0))
            connection.execute("INSERT INTO research_evaluation VALUES (?,?,?,?,?,?)",
                               ("post", "JC", "2026-09-09T21:00:00+08:00",
                                "2026-09-09T20:00:00+08:00", 1, 0))
            stats = market_statistics(connection)
            self.assertEqual(stats["JC"]["samples"], 0)
            self.assertEqual(stats["BD"]["samples"], 1)
            self.assertEqual(stats["BD_EXCLUDE_JC_NOT_EXCLUDED"]["hit_rate"], 1.0)
        finally:
            connection.close()

    def test_daily_runner_and_unchanged_hash_upgrade(self):
        from draw_exclusion.run_daily import run
        football = self.root / "football"
        target = football / "draw_exclusion"
        target.mkdir(parents=True)
        source = Path(__file__).resolve().parents[1] / "draw_exclusion"
        shutil.copytree(source / "config", target / "config")
        (target / "manual_labels.json").write_text('{"labels":[]}')
        (target / "forensic_evidence.json").write_text('{"items":[]}')
        html = fixture_html()
        response = HttpSnapshot("https://example.test", datetime(2026, 9, 8, 9, tzinfo=timezone.utc),
                                html.encode(), None, None, "text/html", 200)
        with patch("draw_exclusion.run_daily.collect", return_value=response), patch(
            "draw_exclusion.run_daily.TitanAdapter"
        ) as adapter:
            adapter.return_value.resolve.return_value = {"status": "not_found"}
            first = run(football)
        self.assertTrue(first["promoted"])
        self.assertEqual(first["qc"]["row_count"], 3)
        self.assertTrue(first["qc"]["invariants_ok"])
        self.assertEqual(first["foreign_key_violations"], 0)
        frozen = {p: p.read_bytes() for p in (target / "raw").rglob("*.html")}
        versions = {p: p.read_bytes() for p in (target / "daily/versions").rglob("*.json")}
        (target / "index.json").write_text('{"schema_version":"2.0"}')
        second_response = replace(response, captured_at_utc=datetime(2026, 9, 8, 9, 1, tzinfo=timezone.utc))
        with patch("draw_exclusion.run_daily.collect", return_value=second_response), patch(
            "draw_exclusion.run_daily.TitanAdapter"
        ) as adapter:
            adapter.return_value.resolve.return_value = {"status": "not_found"}
            second = run(football)
        self.assertFalse(second["promoted"])
        self.assertTrue(second["same_hash_as_previous"])
        self.assertEqual(json.loads((target / "index.json").read_text())["schema_version"], "3.0")
        for path, content in {**frozen, **versions}.items():
            self.assertEqual(path.read_bytes(), content)
