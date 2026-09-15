from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import timedelta
from hashlib import sha256
import json
import math
from pathlib import Path
import sqlite3
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.team_goal_baselines.engine import (  # noqa: E402
    DEFAULT_VARIANTS,
    ENGINE_VERSION,
    FIVE_LEAGUES,
    Match,
    build_snapshot,
    json_dumps,
    load_completed_matches,
    matchup_lambda,
    poisson_nll,
)
from gpt.quant_core import build_quant_packet  # noqa: E402
from gpt.stage14_bayesian import build_market_cluster_likelihood  # noqa: E402


def file_sha256(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class Metrics:
    def __init__(self) -> None:
        self.n = 0
        self.nll = self.total_abs = self.margin_abs = 0.0
        self.home_sq = self.away_sq = self.total_bias = self.margin_bias = 0.0
        self.promoted_n = self.promoted_nll = 0

    def add(self, m: Match, pred: dict[str, Any]) -> None:
        lh, la = pred["lambda_home"], pred["lambda_away"]
        self.n += 1
        nll = poisson_nll(m.home_goals, lh) + poisson_nll(m.away_goals, la)
        self.nll += nll
        self.total_abs += abs((lh + la) - (m.home_goals + m.away_goals))
        self.margin_abs += abs((lh - la) - (m.home_goals - m.away_goals))
        self.home_sq += (lh - m.home_goals) ** 2
        self.away_sq += (la - m.away_goals) ** 2
        self.total_bias += (lh + la) - (m.home_goals + m.away_goals)
        self.margin_bias += (lh - la) - (m.home_goals - m.away_goals)
        if "PROMOTED_OR_NEW" in pred["home_history_class"] or "PROMOTED_OR_NEW" in pred["away_history_class"]:
            self.promoted_n += 1
            self.promoted_nll += nll

    def as_dict(self) -> dict[str, Any]:
        n = max(1, self.n)
        return {
            "n": self.n,
            "poisson_score_nll": self.nll / n if self.n else None,
            "total_goals_mae": self.total_abs / n if self.n else None,
            "goal_margin_mae": self.margin_abs / n if self.n else None,
            "home_goals_rmse": math.sqrt(self.home_sq / n) if self.n else None,
            "away_goals_rmse": math.sqrt(self.away_sq / n) if self.n else None,
            "total_goals_bias": self.total_bias / n if self.n else None,
            "goal_margin_bias": self.margin_bias / n if self.n else None,
            "promoted_or_new_fixture_n": self.promoted_n,
            "promoted_or_new_fixture_nll": self.promoted_nll / self.promoted_n if self.promoted_n else None,
        }


def split_for(season_start: int) -> str:
    if season_start in (2022, 2023):
        return "train"
    if season_start == 2024:
        return "validation"
    if season_start == 2025:
        return "test"
    return "warmup"


def raw_aggregates(matches: list[Match]) -> tuple[list[tuple], list[tuple], list[tuple]]:
    league_rows: list[tuple] = []
    team_rows: list[tuple] = []
    alias_counter: Counter[tuple[str, str, str]] = Counter()
    grouped: dict[tuple[str, int], list[Match]] = defaultdict(list)
    for m in matches:
        grouped[(m.competition_id, m.season_start)].append(m)
        alias_counter[(m.competition_id, m.home_team_id, m.home_team)] += 1
        alias_counter[(m.competition_id, m.away_team_id, m.away_team)] += 1
    for (cid, ss), rows in sorted(grouped.items()):
        n = len(rows)
        hg, ag = sum(m.home_goals for m in rows), sum(m.away_goals for m in rows)
        league_rows.append((cid, FIVE_LEAGUES[cid][0], rows[0].season, ss, n, hg / n, ag / n, (hg + ag) / n, (hg + ag) / (2 * n), (hg + ag) / (2 * n)))
        teams = sorted({t for m in rows for t in (m.home_team_id, m.away_team_id)})
        for team_id in teams:
            home = [m for m in rows if m.home_team_id == team_id]
            away = [m for m in rows if m.away_team_id == team_id]
            gf = sum(m.home_goals for m in home) + sum(m.away_goals for m in away)
            ga = sum(m.away_goals for m in home) + sum(m.home_goals for m in away)
            team_rows.append((cid, rows[0].season, ss, team_id, len(home) + len(away), gf, ga,
                              len(home), sum(m.home_goals for m in home), sum(m.away_goals for m in home),
                              len(away), sum(m.away_goals for m in away), sum(m.home_goals for m in away)))
    alias_rows = [(cid, tid, alias, count) for (cid, tid, alias), count in sorted(alias_counter.items())]
    return league_rows, team_rows, alias_rows


def backtest(matches: list[Match]) -> tuple[list[tuple], dict[str, Any], dict[str, str]]:
    by_league: dict[str, list[Match]] = defaultdict(list)
    for m in matches:
        by_league[m.competition_id].append(m)
    prediction_rows: list[tuple] = []
    report: dict[str, Any] = {}
    selected: dict[str, str] = {}
    for cid, league_rows in sorted(by_league.items()):
        metrics: dict[tuple[str, str], Metrics] = defaultdict(Metrics)
        for target in league_rows:
            if target.season_start < 2022:
                continue
            history = [m for m in league_rows if m.kickoff < target.kickoff]
            for variant, params in DEFAULT_VARIANTS.items():
                try:
                    snap = build_snapshot(history, as_of=target.kickoff, season_start=target.season_start,
                                          variant=variant, params=params)
                except Exception:
                    continue
                pred = matchup_lambda(snap, target.home_team_id, target.away_team_id)
                split = split_for(target.season_start)
                metrics[(variant, split)].add(target, pred)
                metrics[(variant, "all_oos")].add(target, pred)
                prediction_rows.append((
                    target.match_id, cid, target.season, target.season_start,
                    target.kickoff.isoformat(sep=" "), target.home_team_id, target.away_team_id,
                    target.home_goals, target.away_goals, variant, json_dumps(params), split,
                    pred["lambda_home"], pred["lambda_away"], pred["expected_total_goals"],
                    pred["expected_net_goal_difference_home"], pred["home_history_class"],
                    pred["away_history_class"], pred["home_sample_games"], pred["away_sample_games"],
                ))
        league_report: dict[str, Any] = {}
        for variant in DEFAULT_VARIANTS:
            league_report[variant] = {
                split: metrics[(variant, split)].as_dict()
                for split in ("train", "validation", "test", "all_oos")
            }
        eligible = [v for v in DEFAULT_VARIANTS if league_report[v]["train"]["n"]]
        winner = min(eligible, key=lambda v: league_report[v]["train"]["poisson_score_nll"])
        selected[cid] = winner
        report[cid] = {
            "competition": FIVE_LEAGUES[cid][0],
            "selected_on_train_only": winner,
            "selection_metric": "poisson_score_nll",
            "variants": league_report,
        }
    return prediction_rows, report, selected


def _market_calibration(source: Path, matches: list[Match], predictions: list[tuple], selected: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    """Build league-specific Train-only residual scales from Titan closing 1X2+OU."""
    by_key = {(str(row[0]), str(row[9])): row for row in predictions if str(row[11]) == "train"}
    by_cid: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    con = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    ids = {"Pinnacle": ("177", "47"), "Bet365": ("281", "8"), "Macau": ("80", "1")}
    try:
        for m in matches:
            if m.season_start not in (2022, 2023):
                continue
            variant = selected.get(m.competition_id)
            pred = by_key.get((m.match_id, variant or ""))
            if pred is None:
                continue
            companies: dict[str, Any] = {}
            for name, (euro_id, ou_id) in ids.items():
                euro = con.execute("SELECT * FROM european_odds WHERE match_id=? AND company_id=? ORDER BY record_id LIMIT 1", (m.match_id, euro_id)).fetchone()
                ou = con.execute("SELECT * FROM over_under_odds WHERE match_id=? AND company_id=? ORDER BY row_key LIMIT 1", (m.match_id, ou_id)).fetchone()
                if euro is None or ou is None:
                    continue
                try:
                    odds = [float(euro[k]) for k in ("closing_home", "closing_draw", "closing_away")]
                    line_raw = ou["closing_line"]
                    line = float(line_raw) if "/" not in str(line_raw) else sum(float(x) for x in str(line_raw).split("/")) / 2
                    over, under = 1.0 + float(ou["closing_over"]), 1.0 + float(ou["closing_under"])
                    if min(odds) <= 1 or over <= 1 or under <= 1:
                        continue
                    companies[name] = {"one_x_two": odds, "ou": {"line": line, "over": over, "under": under}}
                except (TypeError, ValueError):
                    continue
            if not companies:
                continue
            try:
                packet = build_quant_packet({"match_id": m.match_id, "companies": companies})
                cluster = build_market_cluster_likelihood(packet)
                if cluster.get("status") != "VALID":
                    continue
                mh, ma = map(float, cluster["mean_lambda"])
                hh, ha = float(pred[12]), float(pred[13])
                for axis, value in (("home", mh - hh), ("away", ma - ha), ("total", (mh + ma) - (hh + ha)), ("margin", (mh - ma) - (hh - ha))):
                    by_cid[m.competition_id][axis].append(value)
            except Exception:
                continue
    finally:
        con.close()
    out: dict[str, list[dict[str, Any]]] = {}
    for cid, axes in by_cid.items():
        rows: list[dict[str, Any]] = []
        for axis, values in axes.items():
            values = sorted(values)
            n = len(values)
            median = values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2
            deviations = sorted(abs(v - median) for v in values)
            mad = deviations[n // 2] if n % 2 else (deviations[n // 2 - 1] + deviations[n // 2]) / 2
            def pct(q: float) -> float:
                pos = q * (n - 1); lo, hi = int(pos), min(n - 1, int(pos) + 1)
                return values[lo] + (values[hi] - values[lo]) * (pos - lo)
            rows.append({"competition_id": cid, "axis": axis, "n": n, "median": median, "mad": mad,
                         "robust_sd": max(1e-6, 1.4826 * mad), "p10": pct(.10), "p25": pct(.25),
                         "p75": pct(.75), "p90": pct(.90), "calibration_split": "TRAIN_2022_2023",
                         "source": "TITAN_CLOSING_1X2_OU_LOG_RATE_CLUSTER"})
        out[cid] = rows
    return out


SCHEMA = """
CREATE TABLE metadata (key TEXT PRIMARY KEY, value_json TEXT NOT NULL);
CREATE TABLE source_audit (key TEXT PRIMARY KEY, value_json TEXT NOT NULL);
CREATE TABLE team_aliases (competition_id TEXT, team_id TEXT, alias TEXT, appearances INTEGER,
  PRIMARY KEY (competition_id, team_id, alias));
CREATE INDEX idx_team_alias ON team_aliases(competition_id, alias);
CREATE TABLE league_season_baselines (
  competition_id TEXT, competition TEXT, season TEXT, season_start INTEGER, matches INTEGER,
  home_goals_per_match REAL, away_goals_per_match REAL, total_goals_per_match REAL,
  team_goals_for_per_match REAL, team_goals_against_per_match REAL,
  PRIMARY KEY (competition_id, season_start));
CREATE TABLE team_season_stats (
  competition_id TEXT, season TEXT, season_start INTEGER, team_id TEXT,
  matches INTEGER, gf INTEGER, ga INTEGER,
  home_matches INTEGER, home_gf INTEGER, home_ga INTEGER,
  away_matches INTEGER, away_gf INTEGER, away_ga INTEGER,
  PRIMARY KEY (competition_id, season_start, team_id));
CREATE TABLE backtest_predictions (
  match_id TEXT, competition_id TEXT, season TEXT, season_start INTEGER, kickoff TEXT,
  home_team_id TEXT, away_team_id TEXT, home_goals INTEGER, away_goals INTEGER,
  variant TEXT, params_json TEXT, split TEXT, lambda_home REAL, lambda_away REAL,
  expected_total_goals REAL, expected_net_goal_difference_home REAL,
  home_history_class TEXT, away_history_class TEXT, home_sample_games REAL, away_sample_games REAL,
  PRIMARY KEY (match_id, variant));
CREATE INDEX idx_backtest_lookup ON backtest_predictions(competition_id, season_start, variant);
CREATE TABLE backtest_metrics (
  competition_id TEXT, variant TEXT, split TEXT, n INTEGER, poisson_score_nll REAL,
  total_goals_mae REAL, goal_margin_mae REAL, home_goals_rmse REAL, away_goals_rmse REAL,
  total_goals_bias REAL, goal_margin_bias REAL, promoted_or_new_fixture_n INTEGER,
  promoted_or_new_fixture_nll REAL, PRIMARY KEY (competition_id, variant, split));
CREATE TABLE selected_variants (
  competition_id TEXT PRIMARY KEY, competition TEXT, selected_variant TEXT,
  selection_split TEXT, selection_metric TEXT, research_only INTEGER);
CREATE TABLE market_residual_calibration (
  competition_id TEXT, axis TEXT, n INTEGER, median REAL, mad REAL, robust_sd REAL,
  p10 REAL, p25 REAL, p75 REAL, p90 REAL, calibration_split TEXT, source TEXT,
  PRIMARY KEY (competition_id, axis));
CREATE TABLE latest_league_baselines (
  competition_id TEXT, competition TEXT, variant TEXT, params_json TEXT, as_of TEXT,
  season_start INTEGER, effective_matches REAL, home_goals_per_match REAL,
  away_goals_per_match REAL, total_goals_per_match REAL,
  PRIMARY KEY (competition_id, variant));
CREATE TABLE latest_team_baselines (
  competition_id TEXT, variant TEXT, team_id TEXT, canonical_name TEXT, history_class TEXT,
  matches REAL, gf REAL, ga REAL, gf_per_game REAL, ga_per_game REAL,
  home_matches REAL, home_gf REAL, home_ga REAL, home_gf_per_game REAL, home_ga_per_game REAL,
  away_matches REAL, away_gf REAL, away_ga REAL, away_gf_per_game REAL, away_ga_per_game REAL,
  home_attack_strength REAL, home_defence_concession_factor REAL,
  away_attack_strength REAL, away_defence_concession_factor REAL,
  PRIMARY KEY (competition_id, variant, team_id));
"""


def write_database(path: Path, matches: list[Match], audit: dict[str, Any], source_hash: str,
                   predictions: list[tuple], report: dict[str, Any], selected: dict[str, str],
                   calibration: dict[str, list[dict[str, Any]]]) -> None:
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    league_rows, team_rows, aliases = raw_aggregates(matches)
    canonical_names: dict[tuple[str, str], str] = {}
    counts: dict[tuple[str, str], list[tuple[int, str]]] = defaultdict(list)
    for cid, tid, alias, n in aliases:
        counts[(cid, tid)].append((n, alias))
    for key, values in counts.items():
        canonical_names[key] = max(values, key=lambda x: (x[0], x[1]))[1]

    with sqlite3.connect(path) as con:
        con.executescript(SCHEMA)
        metadata = {
            "engine_version": ENGINE_VERSION,
            "status": "RESEARCH_ONLY_NOT_MODEL_1_WEIGHT_AUTHORITY",
            "source_policy": "TITAN_HISTORICAL_RESULTS_ONLY",
            "source_sha256": source_hash,
            "formula": "lambda_home=league_home_avg*home_attack_strength*away_defence_concession_factor; lambda_away=league_away_avg*away_attack_strength*home_defence_concession_factor",
            "defence_semantics": "concession factor; below 1 is stronger defence",
            "market_goal_residual": "(market_lambda_home-market_lambda_away)-(historical_lambda_home-historical_lambda_away)",
            "market_total_residual": "(market_lambda_home+market_lambda_away)-(historical_lambda_home+historical_lambda_away)",
            "variants": DEFAULT_VARIANTS,
            "anti_leakage": "every backtest snapshot uses kickoff strictly before target kickoff; selection uses 2022-23 and 2023-24 only",
        }
        con.executemany("INSERT INTO metadata VALUES (?,?)", [(k, json_dumps(v)) for k, v in metadata.items()])
        con.executemany("INSERT INTO source_audit VALUES (?,?)", [(k, json_dumps(v)) for k, v in audit.items()])
        con.executemany("INSERT INTO team_aliases VALUES (?,?,?,?)", aliases)
        con.executemany("INSERT INTO league_season_baselines VALUES (?,?,?,?,?,?,?,?,?,?)", league_rows)
        con.executemany("INSERT INTO team_season_stats VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", team_rows)
        con.executemany("INSERT INTO backtest_predictions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", predictions)
        metric_rows = []
        for cid, block in report.items():
            for variant, splits in block["variants"].items():
                for split, m in splits.items():
                    metric_rows.append((cid, variant, split, m["n"], m["poisson_score_nll"], m["total_goals_mae"],
                                        m["goal_margin_mae"], m["home_goals_rmse"], m["away_goals_rmse"],
                                        m["total_goals_bias"], m["goal_margin_bias"], m["promoted_or_new_fixture_n"],
                                        m["promoted_or_new_fixture_nll"]))
        con.executemany("INSERT INTO backtest_metrics VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", metric_rows)
        con.executemany("INSERT INTO selected_variants VALUES (?,?,?,?,?,1)",
                        [(cid, FIVE_LEAGUES[cid][0], v, "train:2022-23+2023-24", "poisson_score_nll") for cid, v in selected.items()])
        calibration_rows = []
        for cid, rows in calibration.items():
            calibration_rows.extend((cid, r["axis"], r["n"], r["median"], r["mad"], r["robust_sd"], r["p10"], r["p25"], r["p75"], r["p90"], r["calibration_split"], r["source"]) for r in rows)
        con.executemany("INSERT INTO market_residual_calibration VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", calibration_rows)

        by_league: dict[str, list[Match]] = defaultdict(list)
        for m in matches:
            by_league[m.competition_id].append(m)
        latest_league, latest_teams = [], []
        for cid, rows in sorted(by_league.items()):
            as_of = max(m.kickoff for m in rows) + timedelta(seconds=1)
            season_start = max(m.season_start for m in rows)
            for variant, params in DEFAULT_VARIANTS.items():
                snap = build_snapshot(rows, as_of=as_of, season_start=season_start, variant=variant, params=params)
                latest_league.append((cid, FIVE_LEAGUES[cid][0], variant, json_dumps(params), snap["as_of"], season_start,
                                      snap["league_games_effective"], snap["league_home_goals_per_match"],
                                      snap["league_away_goals_per_match"], snap["league_total_goals_per_match"]))
                for tid, s in snap["teams"].items():
                    latest_teams.append((cid, variant, tid, canonical_names.get((cid, tid), tid), s["history_class"],
                                         s["games"], s["gf"], s["ga"], s["gf_per_game"], s["ga_per_game"],
                                         s["home_games"], s["home_gf"], s["home_ga"], s["home_gf_per_game"], s["home_ga_per_game"],
                                         s["away_games"], s["away_gf"], s["away_ga"], s["away_gf_per_game"], s["away_ga_per_game"],
                                         s["home_attack_strength"], s["home_defence_concession_factor"],
                                         s["away_attack_strength"], s["away_defence_concession_factor"]))
        con.executemany("INSERT INTO latest_league_baselines VALUES (?,?,?,?,?,?,?,?,?,?)", latest_league)
        con.executemany("INSERT INTO latest_team_baselines VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", latest_teams)


def markdown_report(report: dict[str, Any], audit: dict[str, Any], source_hash: str) -> str:
    lines = [
        "# Titan 五大联赛球队进球基准研究", "",
        f"- 引擎：`{ENGINE_VERSION}`",
        f"- 历史源：单一 Titan SQLite，SHA-256 `{source_hash}`",
        f"- 五大联赛可用比赛：{audit['usable_matches_big5']:,}",
        f"- 无效/缺失赛果：{audit['excluded_invalid_or_missing_result']}；重复 match_id：{audit['excluded_duplicate_match_id']}；重复自然赛程键：{audit['excluded_duplicate_fixture']}",
        "- 状态：RESEARCH ONLY；未修改 MODEL_1 固定权重。", "",
        "## 方法", "",
        "每场严格只使用开赛前记录。主队 λ = 联赛同期主场均值 × 主队主场攻击强度 × 客队客场失球因子；客队 λ 对称。防守指标是失球因子，小于 1 表示防守强。",
        "四方案分别为五年普通均值、近两季、365 日半衰期时间衰减、当前赛季加 10 场历史等效样本收缩。所有基础率均用 5 场联赛均值伪样本处理小样本；新升班/新球队回退联赛均值，重返顶级联赛球队保留本联赛历史。", "",
        "方案选择只看 2022-23 与 2023-24；2024-25 为验证，2025-26 为测试。NLL 越低越好。", "",
        "## 回测结果", "",
        "| 联赛 | 训练选中 | Train NLL | Validation NLL | Test NLL | Test Total MAE | Test Margin MAE |", "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for cid in sorted(report, key=int):
        block = report[cid]
        v = block["selected_on_train_only"]
        m = block["variants"][v]
        lines.append(f"| {block['competition']} | {v} | {m['train']['poisson_score_nll']:.4f} | {m['validation']['poisson_score_nll']:.4f} | {m['test']['poisson_score_nll']:.4f} | {m['test']['total_goals_mae']:.4f} | {m['test']['goal_margin_mae']:.4f} |")
    lines += ["", "## 市场比较字段", "",
              "`market_goal_residual = 市场预期净胜球差 - 历史预期净胜球差`；`market_total_residual = 市场预期总进球 - 历史预期总进球`。同时输出主/客 λ 残差，避免把方向与总量混为一谈。",
              "", "完整逐方案、逐联赛、逐时间分割指标和逐场赛前预测均存放于 SQLite。"]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output", default="database/research/team_goal_baselines.sqlite")
    parser.add_argument("--report-json", default="validation/team_goal_baselines_backtest.json")
    parser.add_argument("--report-md", default="docs/TITAN_BIG5_TEAM_GOAL_BASELINES_RESEARCH.md")
    args = parser.parse_args()
    source = Path(args.db).resolve()
    matches, audit = load_completed_matches(source)
    source_hash = file_sha256(source)
    predictions, report, selected = backtest(matches)
    calibration = _market_calibration(source, matches, predictions, selected)
    payload = {
        "engine_version": ENGINE_VERSION, "status": "RESEARCH_ONLY",
        "source_sha256": source_hash, "source_audit": audit,
        "split": {"warmup": 2021, "train": [2022, 2023], "validation": 2024, "test": 2025},
        "selected_variants": selected, "competitions": report,
        "model_1_fixed_weights_modified": False,
        "market_residual_calibration": {cid: len(rows) for cid, rows in calibration.items()},
    }
    output = Path(args.output)
    report_json, report_md = Path(args.report_json), Path(args.report_md)
    write_database(output, matches, audit, source_hash, predictions, report, selected, calibration)
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md.parent.mkdir(parents=True, exist_ok=True)
    report_md.write_text(markdown_report(report, audit, source_hash), encoding="utf-8")
    print(json.dumps({"status": "OK", "database": str(output), "report": str(report_md),
                      "matches": len(matches), "predictions": len(predictions), "selected": selected}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
