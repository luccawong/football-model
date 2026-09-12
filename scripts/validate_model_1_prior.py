from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime
import json
from math import log
from pathlib import Path
import sqlite3
from typing import Any, Mapping

import numpy as np

from gpt.prior_engine import HyperParameters, build_prior_packet_from_model, fit_league_model, load_titan_matches
from gpt.quant_core import asian_handicap_settlement, build_quant_packet, probabilities_1x2, score_grid
from gpt.stage14_bayesian import build_lambda_posterior, build_market_cluster_likelihood, posterior_predictive_grid

# Titan uses different company-id namespaces for 1X2 and VIP AH/OU.
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
            line = _quarter_line(ou["closing_line"] if "closing_line" in ou.keys() else ou["closing_line_raw"])
            # Historical Titan VIP left/right prices are HK odds.  Conversion is
            # explicit and limited to this historical adapter.
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
        # Historical research contract: positive raw anchor means HOME gives;
        # quant_core uses negative home_handicap when HOME gives.
        return -_quarter_line(row[0])
    except (TypeError, ValueError):
        return None


def _outcome(h: int, a: int) -> str:
    return "home" if h > a else ("draw" if h == a else "away")


def _rps(p: Mapping[str, float], outcome: str) -> float:
    order = ("home", "draw", "away")
    obs = {k: 1.0 if k == outcome else 0.0 for k in order}
    c1p, c1o = p["home"], obs["home"]
    c2p, c2o = p["home"] + p["draw"], obs["home"] + obs["draw"]
    return 0.5 * ((c1p - c1o) ** 2 + (c2p - c2o) ** 2)


def _calibration_summary(pred: list[float], obs: list[float], bins: int = 10) -> dict[str, Any]:
    if not pred:
        return {"n": 0, "brier": None, "ece": None, "bins": []}
    p = np.asarray(pred, dtype=float)
    y = np.asarray(obs, dtype=float)
    rows = []
    ece = 0.0
    edges = np.linspace(0.0, 1.0, bins + 1)
    for i in range(bins):
        mask = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= edges[i + 1])
        n = int(mask.sum())
        if not n:
            continue
        mp, my = float(p[mask].mean()), float(y[mask].mean())
        ece += (n / len(p)) * abs(mp - my)
        rows.append({"lo": float(edges[i]), "hi": float(edges[i + 1]), "n": n, "pred": mp, "actual": my})
    return {
        "n": len(pred),
        "brier": float(np.mean((p - y) ** 2)),
        "ece": float(ece),
        "bins": rows,
    }


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
    ah_pred: list[float] = field(default_factory=list)
    ah_obs: list[float] = field(default_factory=list)

    def add(self, grid: np.ndarray, home: int, away: int, home_handicap: float | None) -> None:
        self.n += 1
        if home < grid.shape[0] and away < grid.shape[1]:
            prob = max(float(grid[home, away]), 1e-15)
        else:
            prob = 1e-15
        self.score_nll.append(-log(prob))
        flat = grid.ravel()
        order = np.argsort(flat)[::-1]
        actual_idx = home * grid.shape[1] + away if home < grid.shape[0] and away < grid.shape[1] else -1
        self.top1 += int(len(order) > 0 and int(order[0]) == actual_idx)
        self.top3 += int(actual_idx in set(int(x) for x in order[:3]))

        p = probabilities_1x2(grid)
        result = _outcome(home, away)
        target = {k: 1.0 if k == result else 0.0 for k in ("home", "draw", "away")}
        self.brier_1x2.append(sum((p[k] - target[k]) ** 2 for k in target))
        self.rps.append(_rps(p, result))

        over25 = 0.0
        for h in range(grid.shape[0]):
            for a in range(grid.shape[1]):
                if h + a >= 3:
                    over25 += float(grid[h, a])
        self.ou_pred.append(over25)
        self.ou_obs.append(1.0 if home + away >= 3 else 0.0)

        if home_handicap is not None:
            settlement = asian_handicap_settlement(grid, float(home_handicap))
            # Settlement-equivalent cover score in [0,1]. This preserves quarter
            # lines instead of deleting half-win/half-loss/push observations.
            pred = (
                settlement["full_win"]
                + 0.75 * settlement["half_win"]
                + 0.50 * settlement["push"]
                + 0.25 * settlement["half_loss"]
            )
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
        return {
            "n": self.n,
            "correct_score_NLL": float(np.mean(self.score_nll)) if self.score_nll else None,
            "Top1_exact_score_hit_rate": self.top1 / self.n if self.n else None,
            "Top3_coverage": self.top3 / self.n if self.n else None,
            "1X2_Brier": float(np.mean(self.brier_1x2)) if self.brier_1x2 else None,
            "RPS": float(np.mean(self.rps)) if self.rps else None,
            "OU_over2_5_calibration": _calibration_summary(self.ou_pred, self.ou_obs),
            "AH_cover_equivalent_calibration": _calibration_summary(self.ah_pred, self.ah_obs),
        }


def _prior_grid(prior: Mapping[str, Any], match_id: str, draws: int) -> np.ndarray:
    pseudo = {
        "status": "BAYESIAN_POSTERIOR",
        "mean_log_lambda": prior["mean_log_lambda"],
        "cov_log_lambda": prior["cov_log_lambda"],
        "rho": 0.0,
    }
    out = posterior_predictive_grid(pseudo, match_id=f"PRIOR|{match_id}", draws=draws)
    return np.asarray(out["grid"], dtype=float)


def _market_grid(quant: Mapping[str, Any]) -> np.ndarray | None:
    market = build_market_cluster_likelihood(quant)
    if market.get("status") != "VALID":
        return None
    lh, la = np.exp(np.asarray(market["mean_log_lambda"], dtype=float))
    return score_grid(float(lh), float(la), float(market["rho_market_median"]), max_goals=12)


def _posterior_grid(quant: Mapping[str, Any], prior: Mapping[str, Any], match_id: str, draws: int) -> np.ndarray | None:
    post = build_lambda_posterior(quant, prior)
    if post.get("status") != "BAYESIAN_POSTERIOR":
        return None
    out = posterior_predictive_grid(post, match_id=f"POST|{match_id}", draws=draws)
    return np.asarray(out["grid"], dtype=float)


def _models_for_cutoff(rows: list[dict], selected: Mapping[str, Any], cutoff: datetime, min_matches: int) -> dict[str, Any]:
    out = {}
    for league, raw in selected.items():
        hyper = HyperParameters(float(raw["half_life_days"]), float(raw["team_sd"]), float(raw["transition_sd"]))
        try:
            out[league] = fit_league_model(
                rows, league=league, as_of=cutoff, hyperparameters=hyper, min_matches=min_matches
            )
        except Exception:
            continue
    return out


def _evaluate_period(
    con: sqlite3.Connection,
    rows: list[dict],
    *,
    season: str,
    selected: Mapping[str, Any],
    draws: int,
    min_matches: int,
) -> dict[str, Any]:
    target = [r for r in rows if str(r["season"]) == str(season)]
    if not target:
        return {"status": "MISSING", "season": season, "reason": "NO_TARGET_ROWS"}
    cutoff = min(r["match_date"] for r in target)
    models = _models_for_cutoff(rows, selected, cutoff, min_matches)
    all_prior = Metrics()
    common = {"A_market_only": Metrics(), "B_titan_prior_only": Metrics(), "C_prior_plus_market": Metrics()}
    coverage = {"target": len(target), "prior": 0, "market": 0, "common_abc": 0}
    bundesliga_example = None

    for r in target:
        model = models.get(r["league"])
        if model is None:
            continue
        prior = build_prior_packet_from_model(
            model,
            home_team=r["home_team"], away_team=r["away_team"], season=r["season"],
            match_date=r["match_date"], calibration_ref="SEASON_FORWARD_VALIDATION",
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
        grid_a = _market_grid(quant)
        grid_c = _posterior_grid(quant, prior, r["match_id"], draws)
        if grid_a is None or grid_c is None:
            continue
        coverage["market"] += 1
        coverage["common_abc"] += 1
        common["A_market_only"].add(grid_a, r["home_score"], r["away_score"], ah)
        common["B_titan_prior_only"].add(grid_b, r["home_score"], r["away_score"], ah)
        common["C_prior_plus_market"].add(grid_c, r["home_score"], r["away_score"], ah)

        if bundesliga_example is None and r["league"] in {"德甲", "Bundesliga"}:
            def top3(g: np.ndarray) -> list[dict[str, Any]]:
                cells = [(float(g[h, a]), h, a) for h in range(g.shape[0]) for a in range(g.shape[1])]
                cells.sort(reverse=True)
                return [{"score": f"{h}-{a}", "p": p} for p, h, a in cells[:3]]
            bundesliga_example = {
                "match_id": r["match_id"],
                "date": r["match_date"].isoformat(sep=" "),
                "home_team": r["home_team"],
                "away_team": r["away_team"],
                "actual": f"{r['home_score']}-{r['away_score']}",
                "prior_packet": prior,
                "A_top3": top3(grid_a),
                "B_top3": top3(grid_b),
                "C_top3": top3(grid_c),
            }

    return {
        "status": "VALIDATED",
        "season": season,
        "training_cutoff": cutoff.isoformat(sep=" "),
        "market_snapshot_contract": "HISTORICAL_CLOSING_SNAPSHOT_NO_INTRADAY_LIFECYCLE_CLAIM",
        "coverage": coverage,
        "prior_only_all_eligible": all_prior.summary(),
        "common_sample_comparison": {name: metric.summary() for name, metric in common.items()},
        "bundesliga_example": bundesliga_example,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Season-forward validation for MODEL_1 Titan Bayesian prior.")
    parser.add_argument("--db", required=True)
    parser.add_argument("--calibration", default="validation/model_1_prior_calibration.json")
    parser.add_argument("--output", default="validation/model_1_prior_validation.json")
    parser.add_argument("--draws", type=int, default=500)
    parser.add_argument("--min-matches", type=int, default=80)
    args = parser.parse_args()
    if args.draws < 500:
        raise SystemExit("--draws must be >=500 to match Stage14 posterior-predictive safety contract")

    rows, audit = load_titan_matches(args.db)
    calibration = json.loads(Path(args.calibration).read_text(encoding="utf-8"))
    selected = calibration.get("selected_hyperparameters", {})
    split = calibration.get("split", {})
    if not selected or not split.get("validate") or not split.get("test"):
        raise SystemExit("Calibration report does not contain frozen train-only hyperparameters/split")

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    try:
        validate = _evaluate_period(
            con, rows, season=split["validate"][0], selected=selected,
            draws=args.draws, min_matches=args.min_matches,
        )
        test = _evaluate_period(
            con, rows, season=split["test"][0], selected=selected,
            draws=args.draws, min_matches=args.min_matches,
        )
    finally:
        con.close()

    report = {
        "status": "VALIDATED_NO_RANDOM_SHUFFLE",
        "dataset_audit": audit,
        "split": split,
        "hyperparameters_frozen_from_train_only": True,
        "comparison_contract": "A/B/C metrics use identical common-market rows",
        "models": {
            "A": "CORRELATED_MARKET_CLUSTER_RECONSTRUCTION_ONLY",
            "B": "TITAN_HISTORICAL_PRIOR_POSTERIOR_PREDICTIVE_RHO0",
            "C": "TITAN_PRIOR_PLUS_EXISTING_CORRELATED_MARKET_BAYESIAN_POSTERIOR",
        },
        "validate": validate,
        "test": test,
        "limitations": [
            "Historical odds tables provide opening/closing snapshots, not a complete timestamped intraday lifecycle.",
            "OU validation reports fixed Over 2.5 calibration to keep models comparable across different bookmaker lines.",
            "AH calibration uses matches.page_ah_line_raw when it is parseable and preserves quarter-line settlement as a [0,1] equivalent score.",
        ],
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
