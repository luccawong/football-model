import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from draw_exclusion_research.crawler.draw_site_collector import HttpSnapshot
from draw_exclusion_research.crawler.draw_site_parser import parse_page, research_match_id
from draw_exclusion_research.crawler.snapshot_manager import store_snapshot
from draw_exclusion_research.database.repository import compare_and_store_snapshot_diff, connect, insert_snapshot


def fixture_html(jc_labels=(0,), bd_labels=(1,), recommendation_labels=None):
    groups = [list(jc_labels), list(bd_labels)]
    if recommendation_labels is not None:
        groups.append(list(recommendation_labels))
    payload = json.dumps(groups, separators=(",", ":"))
    encoded = ",".join(str(ord(char) + 7) for char in payload)
    row = """
    <tr data-single="{single}" data-key="{key}" data-idx="{idx}">
      <td class="c-idx">1</td><td class="c-no">{number}</td>
      <td class="c-time">{time}</td><td class="c-league">{league}</td>
      <td class="c-team">{home} <span class="rq-badge">(-1)</span> <span class="vs">vs</span> {away} {badge}</td>
      <td class="c-ah"><span class="ah-w">0.93</span><b class="ah-line 让">半球/一球</b><span class="ah-w">0.88</span></td>
      {odds}<td class="c-mark">-</td>
    </tr>"""
    jc = row.format(single="1", key="JC|A|B", idx=0, number="周二001", time="2026-09-08 18:30",
                    league="测试联赛", home="主队", away="客队", badge='<span class="sg-badge">单</span>',
                    odds='<td class="c-jc-odds"><b class="oh">1.8</b>/<b class="od">3.5</b>/<b class="oa">4.2</b></td>')
    bd0 = row.format(single="0", key="BD|1|C|D", idx=0, number="1", time="2026-09-08 19:00",
                    league="北单联赛", home="甲队", away="乙队", badge='<span class="bd-badge">北单</span>', odds="")
    bd1 = row.format(single="0", key="BD|2|E|F", idx=1, number="2", time="2026-09-08 20:00",
                    league="北单联赛", home="丙队", away="丁队", badge="", odds="")
    recommendation_table = '<table id="reftbl"><tbody><tr data-idx="0"><td>推荐页应忽略</td></tr></tbody></table>' if recommendation_labels is not None else ""
    return f"""<html><body><span>更新时间：2026-09-08 15:51</span>
    <table id="tbl"><tbody>{jc}</tbody></table>
    <table id="bdtbl"><tbody>{bd0}{bd1}</tbody></table>
    {recommendation_table}
    <script>var _mk = [{encoded}].map(function (c) {{ return String.fromCharCode(c - 7); }}).join('');</script>
    </body></html>"""


class DrawExclusionTests(unittest.TestCase):
    def test_parser_keeps_positive_and_control_rows(self):
        page = parse_page(fixture_html())
        self.assertEqual(len(page.matches), 3)
        self.assertEqual([m.website_draw_exclusion_label for m in page.matches], [1, 0, 1])
        self.assertEqual(page.matches[0].home_team, "主队")
        self.assertEqual(page.matches[0].away_team, "客队")
        self.assertEqual(page.matches[0].visible_asian_handicap, -0.75)
        self.assertEqual(page.matches[0].visible_draw_1x2, 3.5)

    def test_parser_ignores_appended_recommendation_group(self):
        page = parse_page(fixture_html(recommendation_labels=(0, 1, 2)))
        self.assertEqual(len(page.matches), 3)
        self.assertEqual(page.label_indices, {"JC": (0,), "BD": (1,)})
        self.assertEqual([m.source_market for m in page.matches], ["JC", "BD", "BD"])
        self.assertEqual([m.website_draw_exclusion_label for m in page.matches], [1, 0, 1])

    def test_research_match_id_is_stable_under_nfkc_case_and_spaces(self):
        kickoff = "2026-09-08T18:30:00+08:00"
        one = research_match_id(" EPL ", "Team  A", "Ｂ", kickoff)
        two = research_match_id("epl", "team a", "B", kickoff)
        self.assertEqual(one, two)

    def test_snapshot_versions_do_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = HttpSnapshot("https://example.test", datetime(2026, 9, 8, 9, 0, tzinfo=timezone.utc),
                                 b"one", None, None, "text/html; charset=utf-8", 200)
            same = HttpSnapshot("https://example.test", datetime(2026, 9, 8, 9, 1, tzinfo=timezone.utc),
                                b"one", None, None, "text/html; charset=utf-8", 200)
            changed = HttpSnapshot("https://example.test", datetime(2026, 9, 8, 9, 2, tzinfo=timezone.utc),
                                   b"two", None, None, "text/html; charset=utf-8", 200)
            a = store_snapshot(root, first, None)
            b = store_snapshot(root, same, None)
            c = store_snapshot(root, changed, None)
            self.assertEqual((a.content_version, b.content_version, c.content_version), (1, 1, 2))
            self.assertTrue(b.same_hash_as_previous)
            self.assertFalse(c.same_hash_as_previous)
            self.assertEqual(len(list((root / "raw" / "draw_site" / "2026-09-08").glob("*.html"))), 3)

    def test_database_persists_all_rows_and_binary_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            html = fixture_html()
            http = HttpSnapshot("https://example.test", datetime(2026, 9, 8, 9, 0, tzinfo=timezone.utc),
                                html.encode(), None, None, "text/html; charset=utf-8", 200)
            page = parse_page(html)
            stored = store_snapshot(root, http, page.page_reported_update_time)
            connection = connect(root / "research.db")
            try:
                insert_snapshot(connection, stored, page)
                diff = compare_and_store_snapshot_diff(connection, stored)
                total, positives = connection.execute(
                    "SELECT COUNT(*), SUM(website_draw_exclusion_label) FROM website_labels"
                ).fetchone()
                self.assertEqual((total, positives), (3, 2))
                self.assertIsNone(diff["previous_snapshot_id"])
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            finally:
                connection.close()

    def test_snapshot_diff_detects_label_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            connection = connect(root / "research.db")
            try:
                first_html = fixture_html(jc_labels=(0,), bd_labels=(1,))
                second_html = fixture_html(jc_labels=(), bd_labels=(1,))
                first_http = HttpSnapshot(
                    "https://example.test",
                    datetime(2026, 9, 8, 9, 0, tzinfo=timezone.utc),
                    first_html.encode(), None, None, "text/html; charset=utf-8", 200,
                )
                second_http = HttpSnapshot(
                    "https://example.test",
                    datetime(2026, 9, 8, 9, 1, tzinfo=timezone.utc),
                    second_html.encode(), None, None, "text/html; charset=utf-8", 200,
                )
                first_page = parse_page(first_html)
                first = store_snapshot(root, first_http, first_page.page_reported_update_time)
                insert_snapshot(connection, first, first_page)
                compare_and_store_snapshot_diff(connection, first)
                second_page = parse_page(second_html)
                second = store_snapshot(root, second_http, second_page.page_reported_update_time)
                insert_snapshot(connection, second, second_page)
                diff = compare_and_store_snapshot_diff(connection, second)
                self.assertEqual(len(diff["label_changed"]), 1)
                self.assertEqual(diff["label_changed"][0]["from"], 1)
                self.assertEqual(diff["label_changed"][0]["to"], 0)
                self.assertEqual((len(diff["added"]), len(diff["deleted"]), len(diff["odds_changed"])), (0, 0, 0))
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
