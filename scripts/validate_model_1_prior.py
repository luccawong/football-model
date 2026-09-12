from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime
import json
from math import exp, log
from pathlib import Path
import sqlite3
from typing import Any, Mapping

import numpy as np

from gpt.prior_competition import load_competition_store, save_competition_store
from gpt.prior_engine import HyperParameters, build_prior_packet_from_model, fit_league_model, load_titan_matches
from gpt.quant_core import asian_handicap_settlement, build_quant_packet, probabilities_1x2, score_grid
from gpt.stage14_bayesian import build_lambda_posterior, build_market_cluster_likelihood, posterior_predictive_grid

CORE_IDS = {
    "Pinnacle": {"euro": "177", "vip": "47"},
    "Bet365": {"euro": "281", "vip": "8"},
    "Macau": {"euro": "80", "vip": "1"},
}


def _columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {str(r[1]) for r in con.execute(f"PRAGMA table_info({table})")}


def _fetch_company_row(con: sqlite3.Connection, table: str, match_id: str, company_id: str) -> sqlite3.Row | None:
    cols = _columns(con, table)
    if not {"match_id", "company_id"}.issubset(cols):
        return None
    order = ""
    if "company_raw" in cols:
        order = " ORDER BY CASE WHEN company_raw IS NOT NULL AND TRIM(company_raw)<>'' THEN 0 ELSE 1 END"
    rows = con.execute(
        f"SELECT * FROM {table} WHERE CAST(match_id AS TEXT)=? AND CAST(company_id AS TEXT)=?{order} LIMIT 1",
        (str(match_id), str(company_id)),
    ).fetchall()
    return rows[0] if rows else None


def _quarter_line(value: Any) -> float:
    if value is None:
        raise ValueError("line missing")
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if "/" in text:
        vals = [float(x) for x in text.split("/")]
        return float(sum(vals) / len(vals))
    return float(text)


def _historical_market_payload(con: sqlite3.Connection, match_id: str) -> dict[str, Any] | None:
    companies: dict[str, Any] = {}
    for name, ids in CORE_IDS.items():
        euro = _fetch_company_row(con, "european_odds", match_id, ids["euro"])
        ou = _fetch_company_row(con, "over_under_odds", match_id, ids["vip"])
        if euro is None or ou is None:
            continue
        try:
            one_x_two = [float(euro[k]) for k in ("closing_home", "closing_draw", "closing_away")]
            if not all(x > 1.0 and np.isfinite(x) for x in one_x_two):
                continue
            line_key = "closing_line" if "closing_line" in ou.keys() else "closing_line_raw"
            line = _quarter_line(ou[line_key])
            over = 1.0 + float(ou["closing_over"])
            under = 1.0 + float(ou["closing_under"])
            if not (over > 1.0 and under > 1.0 and np.isfinite(over) and np.isfinite(under)):
                continue
            companies[name] = {
                "one_x_two": one_x_two,
                "ou": {"line": line, "over": over, "under": under, "role": "dynamic"},
            }
        except (KeyError, TypeError, ValueError):
            continue
    if not companies:
        return None
    return {"match_id": str(match_id), "companies": companies}


def _page_ah_home_handicap(con: sqlite3.Connection, match_id: str) -> float | None:
    cols = _columns(con, "matches")
    if "page_ah_line_raw" not in cols:
        return None
    row = con.execute(
        "SELECT page_ah_line_raw FROM matches WHERE CAST(match_id AS TEXT)=? LIMIT 1", (str(match_id),)
    ).fetchone()
    if row is None or row[0] is None:
        return None
    try:
        return -_quarter_line(row[0])
    except (TypeError, ValueError):
        return None


def _outcome(h: int, a: int) -> str:
    return "home" if h > a else ("draw" if h == a else "away")


def _rps(p: Mapping[str, float], outcome: str) -> float:
    obs = {k: 1.0 if k == outcome else 0.0 for k in ("home", "draw", "away")}
    return 0.5 * ((p["home"] - obs["home"]) ** 2 + ((p["home"] + p["draw"]) - (obs["home"] + obs["draw"])) ** 2)


def _clip_prob(p: float) -> float:
    return min(max(float(p), 1e-12), 1.0 - 1e-12)


def _calibration_summary(pred: list[float], obs: list[float], bins: int = 10) -> dict[str, Any]:
    if not pred:
        return {"n": 0, "brier": None, "ece": None, "bins": []}
    p = np.asarray(pred, dtype=float)
    y = np.asarray(obs, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows = []
    ece = 0.0
    for i in range(bins):
        mask = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= edges[i + 1])
        n = int(mask.sum())
        if not n:
            continue
        mp, my = float(p[mask].mean()), float(y[mask].mean())
        ece += (n / len(p)) * abs(mp - my)
        rows.append({"lo": float(edges[i]), "hi": float(edges[i + 1]), "n": n, "pred": mp, "actual": my})
    return {"n": len(pred), "brier": float(np.mean((p - y) ** 2)), "ece": float(ece), "bins": rows}


@dataclass
class Metrics:
    n: int = 0
    score_nll: list[float] = field(default_factory=list)
    top1: int = 0
    top3: int = 0
    brier_1x2: list[float] = field(default_factory=list)
    rps: list[float] = field(default_factory=list)
    ou_pred: list[float] = field(default_factory=list)
    ou_obs: list[float] = field(default_factory=list)
    ou_logloss: list[float] = field(default_factory=list)
    ah_pred: list[float] = field(default_factory=list)
    ah_obs: list[float] = field(default_factory=list)

    def merge(self, other: "Metrics") -> None:
        self.n += other.n
        self.score_nll.extend(other.score_nll)
        self.top1 += other.top1
        self.top3 += other.top3
        self.brier_1x2.extend(other.brier_1x2)
        self.rps.extend(other.rps)
        self.ou_pred.extend(other.ou_pred)
        self.ou_obs.extend(other.ou_obs)
        self.ou_logloss.extend(other.ou_logloss)
        self.ah_pred.extend(other.ah_pred)
        self.ah_obs.extend(other.ah_obs)

    def add(self, grid: np.ndarray, home: int, away: int, home_handicap: float | None) -> None:
        self.n += 1
        prob = float(grid[home, away]) if home < grid.shape[0] and away < grid.shape[1] else 1e-15
        self.score_nll.append(-log(max(prob, 1e-15)))
        order = np.argsort(grid.ravel())[::-1]
        actual_idx = home * grid.shape[1] + away if home < grid.shape[0] and away < grid.shape[1] else -1
        self.top1 += int(len(order) > 0 and int(order[0]) == actual_idx)
        self.top3 += int(actual_idx in {int(x) for x in order[:3]})

        p = probabilities_1x2(grid)
        result = _outcome(home, away)
        target = {k: 1.0 if k == result else 0.0 for k in ("home", "draw", "away")}
        self.brier_1x2.append(sum((p[k] - target[k]) ** 2 for k in target))
        self.rps.append(_rps(p, result))

        over25 = sum(float(grid[h, a]) for h in range(grid.shape[0]) for a in range(grid.shape[1]) if h + a >= 3)
        y_over = 1.0 if home + away >= 3 else 0.0
        self.ou_pred.append(over25)
        self.ou_obs.append(y_over)
        cp = _clip_prob(over25)
        self.ou_logloss.append(-(y_over * log(cp) + (1.0 - y_over) * log(1.0 - cp)))

        if home_handicap is not None:
            settlement = asian_handicap_settlement(grid, float(home_handicap))
            pred = settlement["full_win"] + 0.75 * settlement["half_win"] + 0.50 * settlement["push"] + 0.25 * settlement["half_loss"]
            margin = home - away
            q = round(float(home_handicap) * 4) / 4
            nq = int(round(q * 4))
            legs = (q, q) if nq % 2 == 0 else ((nq - 1) / 4, (nq + 1) / 4)
            vals = []
            for leg in legs:
                v = margin + leg
                vals.append(1 if v > 1e-10 else (-1 if v < -1e-10 else 0))
            payoff = sum(vals) / 2.0
            actual = {1.0: 1.0, 0.5: 0.75, 0.0: 0.5, -0.5: 0.25, -1.0: 0.0}[payoff]
            self.ah_pred.append(float(pred))
            self.ah_obs.append(float(actual))

    def summary(self) -> dict[str, Any]:
        ou = _calibration_summary(self.ou_pred, self.ou_obs)
        ah = _calibration_summary(self.ah_pred, self.ah_obs)
        return {
            "n": self.n,
            "correct_score_NLL": float(np.mean(self.score_nll)) if self.score_nll else None,
            "Top1_exact_score_hit_rate": self.top1 / self.n if self.n else None,
            "Top3_coverage": self.top3 / self.n if self.n else None,
            "1X2_Brier": float(np.mean(self.brier_1x2)) if self.brier_1x2 else None,
            "RPS": float(np.mean(self.rps)) if self.rps else None,
            "OU_over2_5_Brier": ou["brier"],
            "OU_over2_5_logloss": float(np.mean(self.ou_logloss)) if self.ou_logloss else None,
            "OU_over2_5_calibration": ou,
            "AH_settlement_aware_Brier": ah["brier"],
            "AH_cover_equivalent_calibration": ah,
        }


def _prior_grid(prior: Mapping[str, Any], match_id: str, draws: int) -> np.ndarray:
    pseudo = {"status": "BAYESIAN_POSTERIOR", "mean_log_lambda": prior["mean_log_lambda"], "cov_log_lambda": prior["cov_log_lambda"], "rho": 0.0}
    out = posterior_predictive_grid(pseudo, match_id=f"PRIOR|{match_id}", draws=draws)
    return np.asarray(out["grid"], dtype=float)


def _market_grid(quant: Mapping[str, Any]) -> tuple[np.ndarray | None, dict[str, Any] | None]:
    market = build_market_cluster_likelihood(quant)
    if market.get("status") != "VALID":
        return None, market
    lh, la = np.exp(np.asarray(market["mean_log_lambda"], dtype=float))
    return score_grid(float(lh), float(la), float(market["rho_market_median"]), max_goals=12), market


def _posterior_grid(quant: Mapping[str, Any], prior: Mapping[str, Any], match_id: str, draws: int) -> tuple[np.ndarray | None, dict[str, Any] | None]:
    post = build_lambda_posterior(quant, prior)
    if post.get("status") != "BAYESIAN_POSTERIOR":
        return None, post
    out = posterior_predictive_grid(post, match_id=f"POST|{match_id}", draws=draws)
    return np.asarray(out["grid"], dtype=float), post


def _top_rows(grid: np.ndarray, n: int) -> list[dict[str, Any]]:
    cells = [(float(grid[h, a]), h, a) for h in range(grid.shape[0]) for a in range(grid.shape[1])]
    cells.sort(reverse=True)
    return [{"score": f"{h}-{a}", "probability": p} for p, h, a in cells[:n]]


def _activation(test: dict[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    minimum = int(policy["activation"]["minimum_common_test_matches_for_active"])
    common = test.get("common_sample_comparison", {})
    a = common.get("A_market_only", {})
    c = common.get("C_prior_plus_market", {})
    n = int(c.get("n") or 0)
    if n < minimum:
        return {"activation": "SHADOW", "reason": "TEST_COMMON_SAMPLE_TOO_SMALL", "common_test_n": n}
    needed = ("correct_score_NLL", "Top3_coverage", "1X2_Brier", "RPS")
    if any(a.get(k) is None or c.get(k) is None for k in needed):
        return {"activation": "SHADOW", "reason": "INCOMPLETE_TEST_METRICS", "common_test_n": n}
    top3_tolerance = float(policy["activation"]["active_gate"]["C_Top3_not_worse_than_A_by_more_than_pp"]) / 100.0
    active = (
        c["correct_score_NLL"] <= a["correct_score_NLL"]
        and c["1X2_Brier"] <= a["1X2_Brier"]
        and c["RPS"] <= a["RPS"]
        and c["Top3_coverage"] >= a["Top3_coverage"] - top3_tolerance
    )
    if active:
        return {"activation": "ACTIVE", "reason": "OOS_RELEASE_GATE_PASSED", "common_test_n": n}
    disabled = (
        c["correct_score_NLL"] > a["correct_score_NLL"] * 1.02
        and c["1X2_Brier"] > a["1X2_Brier"]
        and c["RPS"] > a["RPS"]
    )
    return {
        "activation": "DISABLED" if disabled else "SHADOW",
        "reason": "OOS_MATERIAL_UNDERPERFORMANCE" if disabled else "OOS_RELEASE_GATE_NOT_PASSED",
        "common_test_n": n,
    }


def _evaluate_competition_period(
    con: sqlite3.Connection,
    rows: list[dict],
    *, competition: str, season: str, hyper_raw: Mapping[str, Any],
    draws: int, min_matches: int, want_case: bool,
) -> tuple[dict[str, Any], dict[str, Metrics]]:
    target = [r for r in rows if str(r["league"]) == competition and str(r["season"]) == str(season)]
    if not target:
        return {"status": "MISSING", "competition": competition, "season": season, "reason": "NO_TARGET_ROWS"}, {}
    target.sort(key=lambda r: (r["match_date"], r["match_id"]))
    hyper = HyperParameters(float(hyper_raw["half_life_days"]), float(hyper_raw["team_sd"]), float(hyper_raw["transition_sd"]))
    model_cache: dict[tuple[int, int], Any] = {}
    all_prior = Metrics()
    common = {"A_market_only": Metrics(), "B_titan_prior_only": Metrics(), "C_prior_plus_market": Metrics()}
    coverage = {"target": len(target), "prior": 0, "market": 0, "common_abc": 0}
    case = None

    for r in target:
        key = (r["match_date"].year, r["match_date"].month)
        if key not in model_cache:
            cutoff = datetime(key[0], key[1], 1)
            try:
                model_cache[key] = fit_league_model(rows, league=competition, as_of=cutoff, hyperparameters=hyper, min_matches=min_matches)
            except Exception as exc:
                model_cache[key] = exc
        model = model_cache[key]
        if isinstance(model, Exception):
            continue
        prior = build_prior_packet_from_model(
            model, home_team=r["home_team"], away_team=r["away_team"], season=r["season"],
            match_date=r["match_date"], calibration_ref="COMPETITION_MONTHLY_WALK_FORWARD_OOS",
        )
        ah = _page_ah_home_handicap(con, r["match_id"])
        grid_b = _prior_grid(prior, r["match_id"], draws)
        all_prior.add(grid_b, r["home_score"], r["away_score"], ah)
        coverage["prior"] += 1

        payload = _historical_market_payload(con, r["match_id"])
        if payload is None:
            continue
        try:
            quant = build_quant_packet(payload)
        except Exception:
            continue
        grid_a, market = _market_grid(quant)
        grid_c, post = _posterior_grid(quant, prior, r["match_id"], draws)
        if grid_a is None or grid_c is None or market is None or post is None:
            continue
        coverage["market"] += 1
        coverage["common_abc"] += 1
        common["A_market_only"].add(grid_a, r["home_score"], r["away_score"], ah)
        common["B_titan_prior_only"].add(grid_b, r["home_score"], r["away_score"], ah)
        common["C_prior_plus_market"].add(grid_c, r["home_score"], r["away_score"], ah)

        if want_case and case is None:
            p1x2 = probabilities_1x2(grid_c)
            over25 = sum(float(grid_c[h, a]) for h in range(grid_c.shape[0]) for a in range(grid_c.shape[1]) if h + a >= 3)
            cluster_lambda = [float(exp(x)) for x in market["mean_log_lambda"]]
            posterior_lambda = [float(exp(x)) for x in post["mean_log_lambda"]]
            top10 = _top_rows(grid_c, 10)
            case = {
                "match": {
                    "match_id": r["match_id"], "competition": competition, "season": r["season"],
                    "date": r["match_date"].isoformat(sep=" "), "home": r["home_team"], "away": r["away_team"],
                    "actual_result": f"{r['home_score']}-{r['away_score']}",
                },
                "historical_prior": {
                    "components": prior["components"], "mean_log_lambda": prior["mean_log_lambda"],
                    "cov_log_lambda": prior["cov_log_lambda"], "prior_lambda": prior["mean_lambda"],
                    "hierarchy": prior["hierarchy"],
                },
                "market_likelihood": {
                    "company_reconstruction": quant.get("reconstruction", {}),
                    "cluster_mean_log_lambda": market["mean_log_lambda"],
                    "cluster_cov_log_lambda": market["cov_log_lambda"],
                    "cluster_lambda": cluster_lambda,
                },
                "posterior": {
                    "mean_log_lambda": post["mean_log_lambda"], "cov_log_lambda": post["cov_log_lambda"],
                    "posterior_lambda": posterior_lambda,
                },
                "score": {
                    "raw_top10": top10,
                    "validation_top1": top10[0] if top10 else None,
                    "validation_top2": top10[1] if len(top10) > 1 else None,
                    "validation_top3": top10[2] if len(top10) > 2 else None,
                    "execution_filtered_top3": None,
                    "execution_filter_reason": "FORMAL_AH_EXECUTION_PATH_NOT_AVAILABLE_IN_HISTORICAL_VALIDATION; do not invent one from market AH",
                },
                "metrics": {
                    "Top1_hit": bool(top10 and top10[0]["score"] == f"{r['home_score']}-{r['away_score']}"),
                    "Top3_hit": f"{r['home_score']}-{r['away_score']}" in {x["score"] for x in top10[:3]},
                    "1X2_prediction": p1x2,
                    "AH_home_handicap_reference": ah,
                    "OU_over2_5_probability": over25,
                },
            }

    metric_payload = {name: metric.summary() for name, metric in common.items()}
    return {
        "status": "VALIDATED",
        "competition": competition,
        "season": season,
        "walk_forward": "MONTH_START_REFIT_FIXED_TRAIN_SELECTED_HYPERPARAMETERS",
        "market_snapshot_contract": "HISTORICAL_CLOSING_SNAPSHOT_NO_INTRADAY_LIFECYCLE_CLAIM",
        "coverage": coverage,
        "prior_only_all_eligible": all_prior.summary(),
        "common_sample_comparison": metric_payload,
        "case_study": case,
    }, common


def _render_markdown(report: Mapping[str, Any]) -> str:
    audit = report["dataset_audit"]
    lines = [
        "# MODEL_1 Titan Historical Bayesian Prior Validation — 2026-09-12", "",
        "## Raw Data Audit", "",
        f"- SQLite: `{audit.get('path')}`",
        f"- SHA256: `{audit.get('dataset_sha256')}`",
        f"- raw rows: **{audit.get('matches_count')}**",
        f"- usable completed rows: **{audit.get('usable_completed_matches')}**",
        f"- date range: `{audit.get('usable_date_min')}` → `{audit.get('usable_date_max')}`", "",
        "## Competition Coverage", "",
        "| Competition | Matches | Completed | Seasons | Teams | Home G | Away G | Total G | Missing | Raw status | Activation |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---|---|",
    ]
    status = report.get("competition_status", {})
    for row in report.get("competition_coverage", []):
        s = status.get(row["competition"], {})
        lines.append(
            f"| {row['competition']} | {row['matches']} | {row['completed_matches']} | {', '.join(row.get('seasons', []))} | "
            f"{row['distinct_teams']} | {row['home_goals_mean']:.3f} | {row['away_goals_mean']:.3f} | {row['total_goals_mean']:.3f} | "
            f"{row['missing_scores']} | {row.get('prior_status')} | {s.get('activation')} |"
        )
    lines += ["", "## OOS A/B/C — Test", "",
              "| Competition | N common | A NLL | B NLL | C NLL | A Top3 | B Top3 | C Top3 | A 1X2 Brier | C 1X2 Brier | A RPS | C RPS | Status |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for comp, block in report.get("competition_validation", {}).items():
        test = block.get("test", {}).get("common_sample_comparison", {})
        a, b, c = test.get("A_market_only", {}), test.get("B_titan_prior_only", {}), test.get("C_prior_plus_market", {})
        def f(v: Any) -> str:
            return "NA" if v is None else f"{float(v):.4f}"
        lines.append(
            f"| {comp} | {c.get('n', 0)} | {f(a.get('correct_score_NLL'))} | {f(b.get('correct_score_NLL'))} | {f(c.get('correct_score_NLL'))} | "
            f"{f(a.get('Top3_coverage'))} | {f(b.get('Top3_coverage'))} | {f(c.get('Top3_coverage'))} | "
            f"{f(a.get('1X2_Brier'))} | {f(c.get('1X2_Brier'))} | {f(a.get('RPS'))} | {f(c.get('RPS'))} | "
            f"{report['competition_status'].get(comp, {}).get('activation')} |"
        )
    lines += ["", "## Overall", "", "```json", json.dumps(report.get("overall_test"), ensure_ascii=False, indent=2), "```", "",
              "## Case Studies", ""]
    for comp, case in report.get("case_studies", {}).items():
        lines += [f"### {comp}", "", "```json", json.dumps(case, ensure_ascii=False, indent=2), "```", ""]
    lines += ["## Limitations", ""] + [f"- {x}" for x in report.get("limitations", [])]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Competition-specific season-forward OOS validation for MODEL_1 Titan Bayesian priors.")
    parser.add_argument("--db", required=True)
    parser.add_argument("--calibration", default="validation/model_1_prior_calibration.json")
    parser.add_argument("--store", default="database/priors/model_1_titan_prior_store.json")
    parser.add_argument("--policy", default="config/model_1_prior_policy.json")
    parser.add_argument("--output", default="validation/model_1_prior_validation.json")
    parser.add_argument("--markdown", default="docs/MODEL_1_TITAN_PRIOR_VALIDATION_20260912.md")
    parser.add_argument("--draws", type=int, default=500)
    parser.add_argument("--min-matches", type=int, default=None)
    args = parser.parse_args()
    if args.draws < 500:
        raise SystemExit("--draws must be >=500 to match Stage14 posterior-predictive safety contract")

    rows, audit = load_titan_matches(args.db)
    calibration = json.loads(Path(args.calibration).read_text(encoding="utf-8"))
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    selected = calibration.get("selected_hyperparameters", {})
    splits = calibration.get("split_by_competition", {})
    if not selected or not splits:
        raise SystemExit("Calibration report does not contain competition-specific frozen train-only hyperparameters/splits")
    min_matches = int(args.min_matches or policy.get("minimum_history", {}).get("completed_matches", 80))

    competition_validation: dict[str, Any] = {}
    case_studies: dict[str, Any] = {}
    statuses = {str(k): dict(v) for k, v in calibration.get("competition_status_pre_oos", {}).items()}
    overall = {"A_market_only": Metrics(), "B_titan_prior_only": Metrics(), "C_prior_plus_market": Metrics()}

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    try:
        for competition in calibration.get("competition_universe", []):
            split = splits.get(competition, {})
            hyper = selected.get(competition)
            if hyper is None or split.get("status") != "VALID":
                continue
            validation, _ = _evaluate_competition_period(
                con, rows, competition=competition, season=split["validate"][0], hyper_raw=hyper,
                draws=args.draws, min_matches=min_matches, want_case=False,
            )
            test, test_metrics = _evaluate_competition_period(
                con, rows, competition=competition, season=split["test"][0], hyper_raw=hyper,
                draws=args.draws, min_matches=min_matches, want_case=True,
            )
            competition_validation[competition] = {"split": split, "validation": validation, "test": test}
            if test.get("case_study") is not None:
                case_studies[competition] = test["case_study"]
            pre = statuses.get(competition, {})
            if pre.get("reason") == "GRID_EXTENSION_REQUIRED":
                statuses[competition] = {**pre, "activation": "SHADOW", "reason": "GRID_EXTENSION_REQUIRED"}
            else:
                statuses[competition] = {**pre, **_activation(test, policy)}
            for name, metric in test_metrics.items():
                overall[name].merge(metric)
    finally:
        con.close()

    audit = dict(calibration.get("data_audit", audit))
    report = {
        "status": "COMPETITION_SPECIFIC_OOS_COMPLETE",
        "dataset_audit": audit,
        "competition_universe": calibration.get("competition_universe", []),
        "competition_coverage": calibration.get("competition_coverage", []),
        "split_by_competition": splits,
        "hyperparameters_frozen_from_train_only": True,
        "selected_hyperparameters": selected,
        "competition_validation": competition_validation,
        "competition_status": statuses,
        "overall_test": {name: metric.summary() for name, metric in overall.items()},
        "case_studies": case_studies,
        "comparison_contract": "A/B/C metrics use identical common-market rows within each competition; overall is secondary to competition-level results",
        "limitations": [
            "Historical odds tables provide opening/closing snapshots, not a complete timestamped intraday lifecycle.",
            "OU validation reports Over 2.5 probability/calibration for a common cross-model target; dynamic main-line calibration requires a separate market-line report.",
            "AH validation uses matches.page_ah_line_raw when parseable and preserves quarter-line full/half/push settlement as a [0,1] equivalent target.",
            "Historical validation does not contain MODEL_1's formal pre-match AH execution decision. Therefore case-study execution-filtered Top3 is not fabricated from the market AH reference; the runtime Stage14 hard gate is tested separately.",
            "Activation thresholds are engineering release gates, not statistical-significance claims.",
        ],
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = Path(args.markdown)
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(_render_markdown(report), encoding="utf-8")

    store = load_competition_store(args.store)
    store["competition_status"] = statuses
    store["validation_ref"] = str(out)
    store["validation_report_markdown"] = str(md)
    save_competition_store(store, args.store)

    print(json.dumps({
        "status": report["status"], "output": str(out), "markdown": str(md),
        "competitions": report["competition_universe"],
        "activation": {k: v.get("activation") for k, v in statuses.items()},
        "case_studies": sorted(case_studies),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
