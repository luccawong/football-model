from __future__ import annotations

from collections import Counter
from pathlib import Path

from draw_exclusion_research.crawler.draw_site_parser import ParsedPage
from draw_exclusion_research.crawler.snapshot_manager import StoredSnapshot


def _coverage(connection, table: str, snapshot_id: str) -> int:
    return connection.execute(
        f"""SELECT COUNT(*) FROM website_labels wl
        WHERE wl.snapshot_id=? AND EXISTS (
            SELECT 1 FROM {table} e WHERE e.research_match_id=wl.research_match_id
        )""",
        (snapshot_id,),
    ).fetchone()[0]


def render_daily_report(connection, snapshot: StoredSnapshot, page: ParsedPage) -> str:
    by_market = Counter(match.source_market for match in page.matches)
    excluded = Counter(match.source_market for match in page.matches if match.website_draw_exclusion_label)
    visible_1x2 = sum(match.visible_home_1x2 is not None for match in page.matches)
    visible_ah = sum(match.visible_asian_handicap is not None for match in page.matches)
    resolutions = connection.execute(
        "SELECT status, COUNT(*) n FROM match_resolutions WHERE snapshot_id=? GROUP BY status",
        (snapshot.snapshot_id,),
    ).fetchall()
    resolution_counts = {row["status"]: row["n"] for row in resolutions}
    titan_matched = resolution_counts.get("resolved", 0)
    diff = connection.execute(
        "SELECT * FROM snapshot_diffs WHERE snapshot_id=?",
        (snapshot.snapshot_id,),
    ).fetchone()
    if diff is None or diff["previous_snapshot_id"] is None:
        change_text = "首次采集，无前一快照可比较"
    elif snapshot.same_hash_as_previous:
        change_text = "与前一快照相同"
    else:
        change_text = "与前一快照不同；已作为新版本保存并完成行级比较"
    ext_1x2 = _coverage(connection, "external_1x2", snapshot.snapshot_id)
    ext_ah = _coverage(connection, "external_ah", snapshot.snapshot_id)
    ext_ou = _coverage(connection, "external_ou", snapshot.snapshot_id)
    oddspapi = connection.execute(
        """SELECT COUNT(*) FROM website_labels wl WHERE wl.snapshot_id=? AND EXISTS (
        SELECT 1 FROM external_1x2 e WHERE e.research_match_id=wl.research_match_id AND lower(e.source) LIKE '%oddspapi%')""",
        (snapshot.snapshot_id,),
    ).fetchone()[0]
    unmatched = connection.execute(
        """SELECT wl.source_market, wl.match_number, m.competition, m.home_team, m.away_team,
                  m.kickoff_time, mr.status
        FROM website_labels wl
        JOIN matches m USING (research_match_id)
        JOIN match_resolutions mr USING (snapshot_id, research_match_id, source_market)
        WHERE wl.snapshot_id=? AND mr.status <> 'resolved'
        ORDER BY wl.source_market, wl.site_row_index""",
        (snapshot.snapshot_id,),
    ).fetchall()
    total = len(page.matches)
    lines = [
        f"# Draw Exclusion Daily Report — {snapshot.snapshot_time_beijing[:10]}",
        "",
        "> 本报告只记录赛前可见数据和匹配覆盖，不生成排平规则或比赛预测。",
        "",
        "## Sample Summary",
        "",
        "| 市场 | 总比赛数 | 排平数 | 未排平数 |",
        "|---|---:|---:|---:|",
        f"| 竞彩 | {by_market['JC']} | {excluded['JC']} | {by_market['JC'] - excluded['JC']} |",
        f"| 北单 | {by_market['BD']} | {excluded['BD']} | {by_market['BD'] - excluded['BD']} |",
        f"| 合计（网站行） | {total} | {sum(excluded.values())} | {total - sum(excluded.values())} |",
        "",
        "## Data Coverage",
        "",
        "| 指标 | 覆盖 |",
        "|---|---:|",
        f"| Titan 匹配率 | {titan_matched}/{total} ({(100*titan_matched/total if total else 0):.1f}%) |",
        f"| 外部 1X2 覆盖率 | {ext_1x2}/{total} ({(100*ext_1x2/total if total else 0):.1f}%) |",
        f"| 外部 AH 覆盖率 | {ext_ah}/{total} ({(100*ext_ah/total if total else 0):.1f}%) |",
        f"| 外部 OU 覆盖率 | {ext_ou}/{total} ({(100*ext_ou/total if total else 0):.1f}%) |",
        f"| OddsPapi 覆盖率 | {oddspapi}/{total} ({(100*oddspapi/total if total else 0):.1f}%) |",
        f"| 网站可见 1X2 | {visible_1x2}/{total} ({(100*visible_1x2/total if total else 0):.1f}%) |",
        f"| 网站可见 AH | {visible_ah}/{total} ({(100*visible_ah/total if total else 0):.1f}%) |",
        "",
        "## Website Change Check",
        "",
        f"- Snapshot ID: `{snapshot.snapshot_id}`",
        f"- HTML SHA-256: `{snapshot.sha256}`",
        f"- Content version: `version_{snapshot.content_version}`",
        f"- Page reported update: `{snapshot.page_reported_update_time or 'UNKNOWN'}`",
        f"- HTTP Last-Modified: `{snapshot.last_modified or 'UNKNOWN'}`",
        f"- Change result: {change_text}",
        f"- 新增比赛：{diff['added_rows'] if diff else 0}",
        f"- 删除比赛：{diff['deleted_rows'] if diff else 0}",
        f"- 排平标签变化：{diff['label_changed_rows'] if diff else 0}",
        f"- 网站可见赔率/盘口变化：{diff['odds_changed_rows'] if diff else 0}",
        "",
        "## QC",
        "",
        f"- 网站当前比赛行：{total}",
        f"- 网站排平：{sum(excluded.values())}",
        f"- 网站未排平：{total - sum(excluded.values())}",
        f"- Titan 成功匹配：{titan_matched}",
        f"- Titan 未匹配/不可用：{total - titan_matched}",
        f"- 缺少外部 1X2：{total - ext_1x2}",
        f"- 缺少外部 AH：{total - ext_ah}",
        f"- 缺少外部 OU：{total - ext_ou}",
        f"- 缺少网站可见 1X2：{total - visible_1x2}",
        f"- 缺少网站可见 AH：{total - visible_ah}",
        "",
        "## Missing Data — Titan Unmatched",
        "",
    ]
    if not unmatched:
        lines.append("无。")
    else:
        lines.extend(["| 市场 | 编号 | 赛事 | 对阵 | 开赛时间 | 状态 |", "|---|---|---|---|---|---|"])
        lines.extend(
            f"| {row['source_market']} | {row['match_number']} | {row['competition']} | "
            f"{row['home_team']} vs {row['away_team']} | {row['kickoff_time']} | {row['status']} |"
            for row in unmatched
        )
    lines.extend(
        [
            "",
            "## Leakage Guard",
            "",
            "- Website label frozen at `snapshot_time_utc`.",
            "- No final score is present in feature tables.",
            "- External odds are stored as raw timeline events; future feature builders must filter by `feature_time` and kickoff.",
            "- 竞彩与北单分别统计；本报告的合计只用于 QC，不作为统一模型指标。",
            "",
        ]
    )
    return "\n".join(lines)


def write_daily_report(project_root: Path, snapshot: StoredSnapshot, text: str) -> Path:
    path = project_root / "reports" / "daily" / f"{snapshot.snapshot_time_beijing[:10]}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path
