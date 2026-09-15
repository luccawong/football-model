"""Build the Titan-only MODEL_1 RECENT_FORM V1 research calibration.

The script intentionally evaluates the current Stage14 formal market cluster
against the same cluster plus a strictly pre-kickoff recent-form observation.
It is not a training command for Domestic Prior V2 and it never writes a
production fixed weight.  Hyperparameters and the release gate are frozen from
Train/Validation before Test is evaluated.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import log
from pathlib import Path
import sqlite3
import sys
from typing import Any, Iterable

import numpy as np
from numpy.polynomial.hermite import hermgauss
from scipy.special import gammaln

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gpt.domestic_prior import DOMESTIC
from gpt.prior_competition import file_sha256
from gpt.prior_engine import load_titan_matches
from gpt.quant_core import build_quant_packet, score_grid
from gpt.recent_form import (
    APPROVED_STATUS, ARTIFACT_VERSION, RecentFormFeatureBuilder, RecentMatch,
    canonical_json_sha256,
)
from gpt.stage14_bayesian import _normal_update, build_market_cluster_likelihood
from scripts.validate_model_1_prior import CORE_IDS, Metrics, _quarter_line


RAW_SHA256 = "cb409b3ceb882491671c08abbf6815fdfbaa398010de0377ad1d7bcf0d1531a7"
CALIBRATION_VERSION = "MODEL_1-RECENT-FORM-V1-20260915"
SEASONS = {"train": (2021, 2022, 2023), "validation": (2024,), "test": (2025,)}
FEATURE_GRID = (
    {"window": 5, "half_life_days": 45.0, "shrinkage_matches": 4.0},
    {"window": 5, "half_life_days": 120.0, "shrinkage_matches": 8.0},
    {"window": 10, "half_life_days": 45.0, "shrinkage_matches": 4.0},
    {"window": 10, "half_life_days": 120.0, "shrinkage_matches": 8.0},
)
RIDGE_GRID = (0.25, 1.0, 4.0)
GATE = {
    "version": "RECENT_FORM_V1_FROZEN_BEFORE_TEST",
    "minimum_n": 120,
    "nll_improvement": 0.002,
    "top3_tolerance": 0.01,
    "secondary_tolerance": 0.0005,
    "bootstrap_resamples": 5000,
    "bootstrap_upper_ci": 0.0,
    "placebo_absolute_delta_limit": 0.003,
}


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def _phase_row(row: sqlite3.Row, phase: str, fields: Iterable[str]) -> list[float]:
    return [float(row[f"{phase}_{field}"]) for field in fields]


class TitanMarketArchive:
    """Read only core Stage14 market rows; no all-bookmaker averaging."""

    def __init__(self, db_path: str | Path) -> None:
        self._connection = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
        self._connection.row_factory = sqlite3.Row
        self._euros: dict[tuple[str, str], sqlite3.Row] = {}
        self._ous: dict[tuple[str, str], sqlite3.Row] = {}
        ids_euro = tuple(item["euro"] for item in CORE_IDS.values())
        ids_ou = tuple(item["vip"] for item in CORE_IDS.values())
        for table, ids, output in (("european_odds", ids_euro, self._euros), ("over_under_odds", ids_ou, self._ous)):
            marks = ",".join("?" for _ in ids)
            rows = self._connection.execute(
                f"SELECT * FROM {table} WHERE CAST(company_id AS TEXT) IN ({marks})", ids
            ).fetchall()
            for row in rows:
                key = (str(row["match_id"]), str(row["company_id"]))
                # Deterministic duplicate choice, matching prior validation's
                # preference for an identified bookmaker row.
                existing = output.get(key)
                if existing is None or (not str(existing["company_raw"] or "").strip() and str(row["company_raw"] or "").strip()):
                    output[key] = row
        self._ah = {
            str(row["match_id"]): row["page_ah_line_raw"]
            for row in self._connection.execute("SELECT match_id,page_ah_line_raw FROM matches").fetchall()
        }

    def close(self) -> None:
        self._connection.close()

    def packet(self, match_id: str, phase: str) -> tuple[dict[str, Any] | None, float | None]:
        companies: dict[str, Any] = {}
        for name, ids in CORE_IDS.items():
            euro = self._euros.get((match_id, ids["euro"]))
            ou = self._ous.get((match_id, ids["vip"]))
            if euro is None or ou is None:
                continue
            try:
                one_x_two = _phase_row(euro, phase, ("home", "draw", "away"))
                over, under = [1.0 + x for x in _phase_row(ou, phase, ("over", "under"))]
                line = _quarter_line(ou[f"{phase}_line"])
                if not all(np.isfinite(x) and x > 1.0 for x in one_x_two + [over, under]) or not np.isfinite(line):
                    continue
                companies[name] = {"one_x_two": one_x_two, "ou": {"line": line, "over": over, "under": under, "role": "dynamic"}}
            except (KeyError, TypeError, ValueError):
                continue
        handicap = None
        try:
            if self._ah.get(match_id) is not None:
                handicap = -_quarter_line(self._ah[match_id])
        except (TypeError, ValueError):
            pass
        return ({"match_id": match_id, "companies": companies} if companies else None), handicap


def collect_markets(archive: TitanMarketArchive, rows: Iterable[dict[str, Any]], cache_path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        return {tuple(key.split("|", 1)): value for key, value in cached.items()}
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for index, row in enumerate(rows, 1):
        for phase in ("opening", "closing"):
            payload, handicap = archive.packet(row["match_id"], phase)
            if payload is None:
                continue
            try:
                quant = build_quant_packet(payload, {"report_ou_lines": [], "report_ah_lines": []})
                market = build_market_cluster_likelihood(quant)
            except Exception:  # malformed historical quote is excluded, never repaired
                continue
            if market.get("status") == "VALID":
                result[(row["match_id"], phase)] = {"market": market, "handicap": handicap}
        if index % 1000 == 0:
            print(f"markets {index}", flush=True)
    dump(cache_path, {f"{match_id}|{phase}": value for (match_id, phase), value in result.items()})
    return result


_GH_NODES, _GH_WEIGHTS = hermgauss(9)
_GH_A, _GH_B = np.meshgrid(_GH_NODES, _GH_NODES)
_GH_Z = np.column_stack([_GH_A.ravel(), _GH_B.ravel()]) * np.sqrt(2.0)
_GH_W = np.outer(_GH_WEIGHTS, _GH_WEIGHTS).ravel() / np.pi


def predictive_grid(mean: np.ndarray, covariance: np.ndarray, rho: float) -> np.ndarray:
    """Deterministic lognormal/DC integration matching formal market semantics."""
    chol = np.linalg.cholesky(covariance)
    rates = np.exp(np.clip(_GH_Z @ chol.T + mean, np.log(0.05), np.log(6.0)))
    goals = np.arange(13)
    ph = np.exp(goals * np.log(rates[:, 0, None]) - rates[:, 0, None] - gammaln(goals + 1))
    pa = np.exp(goals * np.log(rates[:, 1, None]) - rates[:, 1, None] - gammaln(goals + 1))
    grids = ph[:, :, None] * pa[:, None, :]
    grids[:, 0, 0] *= 1.0 - rates[:, 0] * rates[:, 1] * rho
    grids[:, 0, 1] *= 1.0 + rates[:, 0] * rho
    grids[:, 1, 0] *= 1.0 + rates[:, 1] * rho
    grids[:, 1, 1] *= 1.0 - rho
    grids = np.maximum(grids, 0.0)
    grids /= grids.sum(axis=(1, 2))[:, None, None]
    output = np.einsum("i,ijk->jk", _GH_W, grids)
    return output / output.sum()


def _target_vector(row: dict[str, Any], market: dict[str, Any]) -> np.ndarray:
    base = np.exp(np.asarray(market["mean_log_lambda"], dtype=float))
    observed = np.asarray([row["home_score"], row["away_score"]], dtype=float)
    # Anscombe-style stabilisation is fitted only within Train folds.
    return np.clip(np.log((observed + 0.5) / base), -1.75, 1.75)


def fit_response(records: list[dict[str, Any]], *, ridge: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if len(records) < 20:
        raise ValueError("INSUFFICIENT_TRAIN_RECORDS")
    x_raw = np.asarray([record["features"] for record in records], dtype=float)
    center = np.median(x_raw, axis=0)
    scale = np.median(np.abs(x_raw - center), axis=0) * 1.4826
    scale = np.where(scale > 0.05, scale, 1.0)
    x = (x_raw - center) / scale
    y = np.asarray([record["target"] for record in records], dtype=float)
    design = np.column_stack([np.ones(len(x)), x])
    penalty = np.diag([0.0, ridge, ridge, ridge, ridge])
    coef = np.linalg.solve(design.T @ design + penalty, design.T @ y)
    intercept, response = coef[0], coef[1:].T
    residuals = y - design @ coef
    cov = np.cov(residuals.T, ddof=1) + np.eye(2) * 0.25
    cov = (cov + cov.T) / 2.0
    return intercept, response, cov, center, scale


def model_grid(record: dict[str, Any], model: dict[str, Any] | None) -> np.ndarray:
    market = record["market"]
    mean = np.asarray(market["mean_log_lambda"], dtype=float)
    covariance = np.asarray(market["cov_log_lambda"], dtype=float)
    if model is not None:
        raw_features = np.asarray(record["features"], dtype=float)
        features = (raw_features - np.asarray(model["center"], dtype=float)) / np.asarray(model["scale"], dtype=float)
        delta = np.asarray(model["intercept"], dtype=float) + np.asarray(model["response"], dtype=float) @ features
        observed_mean = mean + delta
        mean, covariance = _normal_update(mean, covariance, observed_mean, np.asarray(model["covariance"], dtype=float))
    return predictive_grid(mean, covariance, float(market["rho_market_median"]))


def evaluate(records: list[dict[str, Any]], model: dict[str, Any] | None, *, placebo_seed: int | None = None) -> tuple[dict[str, Any], list[dict[str, float]]]:
    ordered = list(records)
    if placebo_seed is not None and model is not None:
        permutation = np.random.default_rng(placebo_seed).permutation(len(ordered))
        ordered = [{**record, "features": records[int(permutation[i])]["features"]} for i, record in enumerate(records)]
    metric = Metrics(); details: list[dict[str, float]] = []
    for record in ordered:
        grid = model_grid(record, model)
        previous_top3 = metric.top3
        metric.add(grid, record["home_score"], record["away_score"], record["handicap"])
        details.append({"nll": metric.score_nll[-1], "top3": float(metric.top3 - previous_top3), "brier": metric.brier_1x2[-1], "rps": metric.rps[-1]})
    return metric.summary(), details


def paired_bootstrap(base: list[dict[str, float]], recent: list[dict[str, float]], *, seed: int) -> dict[str, Any]:
    if len(base) != len(recent) or not base:
        return {"n": 0}
    rng = np.random.default_rng(seed)
    n = len(base)
    output: dict[str, Any] = {"n": n, "resamples": GATE["bootstrap_resamples"], "method": "PAIRED_MATCH_BOOTSTRAP"}
    for key, label in (("nll", "delta_nll"), ("top3", "delta_top3"), ("brier", "delta_1x2_brier"), ("rps", "delta_rps")):
        delta = np.asarray([recent[i][key] - base[i][key] for i in range(n)], dtype=float)
        means = np.mean(delta[rng.integers(0, n, size=(GATE["bootstrap_resamples"], n))], axis=1)
        output[label] = {"mean": float(delta.mean()), "median": float(np.median(means)), "ci95": [float(x) for x in np.quantile(means, (0.025, 0.975))]}
    return output


def frozen_gate(report: dict[str, Any]) -> tuple[bool, list[str]]:
    base, recent, bootstrap = report["base"], report["recent"], report["bootstrap"]
    reasons: list[str] = []
    if int(base["n"]) < GATE["minimum_n"]:
        reasons.append("INSUFFICIENT_OOS_SAMPLE")
    if recent["correct_score_NLL"] > base["correct_score_NLL"] - GATE["nll_improvement"]:
        reasons.append("NLL_IMPROVEMENT_BELOW_FROZEN_THRESHOLD")
    if bootstrap["delta_nll"]["ci95"][1] >= GATE["bootstrap_upper_ci"]:
        reasons.append("NLL_BOOTSTRAP_NOT_STRICTLY_BETTER")
    if recent["Top3_coverage"] < base["Top3_coverage"] - GATE["top3_tolerance"]:
        reasons.append("TOP3_HARM")
    for key in ("1X2_Brier", "RPS", "OU_over2_5_Brier", "AH_settlement_aware_Brier"):
        if base.get(key) is not None and recent.get(key) is not None and recent[key] > base[key] + GATE["secondary_tolerance"]:
            reasons.append(f"SECONDARY_HARM:{key}")
    return not reasons, reasons or ["FROZEN_GATE_PASS"]


def _records_for(rows: list[dict[str, Any]], features: dict[str, dict[str, Any]], markets: dict[tuple[str, str], dict[str, Any]], phase: str, seasons: tuple[int, ...]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        if row["season_start"] not in seasons:
            continue
        market_item = markets.get((row["match_id"], phase)); feature = features.get(row["match_id"])
        if market_item is None or feature is None:
            continue
        output.append({**row, "features": feature["features"], "market": market_item["market"], "handicap": market_item["handicap"], "target": _target_vector(row, market_item["market"])})
    return output


def select_train_only(rows: list[dict[str, Any]], feature_sets: dict[str, dict[str, dict[str, Any]]], markets: dict[tuple[str, str], dict[str, Any]], phase: str) -> tuple[dict[str, Any], dict[str, Any]]:
    trials: list[dict[str, Any]] = []
    for spec_key, feature_rows in feature_sets.items():
        all_train = _records_for(rows, feature_rows, markets, phase, SEASONS["train"])
        for ridge in RIDGE_GRID:
            fold_losses = []
            for fit_seasons, holdout in (((2021,), 2022), ((2021, 2022), 2023)):
                fit = [x for x in all_train if x["season_start"] in fit_seasons]
                hold = [x for x in all_train if x["season_start"] == holdout]
                if len(fit) < 40 or len(hold) < 40:
                    continue
                intercept, response, covariance, center, scale = fit_response(fit, ridge=ridge)
                model = {"intercept": intercept, "response": response, "covariance": covariance, "center": center, "scale": scale}
                summary, _ = evaluate(hold, model)
                fold_losses.append(summary["correct_score_NLL"])
            if len(fold_losses) == 2:
                trials.append({"feature_spec": spec_key, "ridge": ridge, "fold_nll": fold_losses, "mean_nll": float(np.mean(fold_losses))})
    if not trials:
        raise RuntimeError("NO_TRAIN_ONLY_SELECTION_CANDIDATE")
    winner = min(trials, key=lambda item: (item["mean_nll"], item["ridge"], item["feature_spec"]))
    final_train = _records_for(rows, feature_sets[winner["feature_spec"]], markets, phase, SEASONS["train"])
    intercept, response, covariance, center, scale = fit_response(final_train, ridge=float(winner["ridge"]))
    return winner, {"intercept": intercept, "response": response, "covariance": covariance, "center": center, "scale": scale, "train_n": len(final_train)}


def make_artifact(*, competition: str, phase: str, selected: dict[str, Any], model: dict[str, Any], activation: str, reasons: list[str], source_sha: str) -> dict[str, Any]:
    response = np.asarray(model["response"], dtype=float)
    artifact: dict[str, Any] = {
        "artifact_version": ARTIFACT_VERSION, "source_group": "RECENT_FORM", "effect_mode": "QUANTIFIED_OBSERVATION",
        "calibration_ref": f"RECENT_FORM_V1/{competition}/{phase.upper()}", "calibration_version": CALIBRATION_VERSION,
        "competition": competition, "market_phase": phase.upper(), "activation": activation,
        "runtime_eligible": activation == APPROVED_STATUS, "coefficients": response.mean(axis=0).tolist(),
        "response_coefficients": response.tolist(), "intercept": np.asarray(model["intercept"], dtype=float).tolist(),
        "robust_scaler": {"center": np.asarray(model["center"], dtype=float).tolist(), "scale": np.asarray(model["scale"], dtype=float).tolist(), "fit_scope": "TRAIN_ONLY_MEDIAN_MAD"},
        "cov_log_lambda": np.asarray(model["covariance"], dtype=float).tolist(),
        "train_range": "2021-2022..2023-2024", "validation_range": "2024-2025", "test_range": "2025-2026",
        "selection": selected, "activation_reasons": reasons,
        "provenance": {"source": "titan数据库.zip -> football_odds_2021_2026.sqlite", "source_sha256": source_sha,
                       "formal_model_1_weight_impact": "NONE", "team_goal_baseline_usage": "PAST_MATCH_OPPONENT_NORMALIZATION_ONLY",
                       "no_future_leakage": True, "source_match_kickoff_rule": "source_match_kickoff < target_match_kickoff",
                       "market_definition": "STAGE14_CORRELATED_CORE_CLUSTER_PINNACLE_BET365_MACAU"},
    }
    artifact["artifact_sha256"] = canonical_json_sha256(artifact)
    return artifact


def render_doc(summary: dict[str, Any]) -> str:
    lines = ["# MODEL_1 RECENT_FORM V1", "", "Titan-only, research-layer calibration. Stage14 fixed weights remain unchanged.", "",
             "## Frozen design", "", "- Train: 2021-22–2023-24; Validation: 2024-25; Test: 2025-26.",
             "- All feature/ridge choices and release thresholds were frozen before Test.",
             "- Source results obey `source_match_kickoff < target_match_kickoff`; same-kickoff records are batched.",
             "- Market baseline is the Stage14 correlated Pinnacle + Bet365 + Macau log-rate cluster, separately for OPENING/CLOSING.", "",
             "## OOS results", "", "| League | Phase | Split | N | Base NLL | Recent NLL | Delta NLL | Base/Recent Top3 | Base/Recent 1X2 Brier | Base/Recent RPS | Base/Recent OU Brier | Base/Recent AH Brier | Activation |", "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for league, value in summary["leagues"].items():
        for phase, item in value.items():
            if phase not in ("opening", "closing"): continue
            for split in ("validation", "test"):
                report = item[split]; base, recent = report["base"], report["recent"]
                pair = lambda key, digits=4: f"{base[key]:.{digits}f}/{recent[key]:.{digits}f}" if base.get(key) is not None and recent.get(key) is not None else "NA"
                lines.append(f"| {league} | {phase.upper()} | {split} | {base['n']} | {base['correct_score_NLL']:.4f} | {recent['correct_score_NLL']:.4f} | {recent['correct_score_NLL']-base['correct_score_NLL']:.4f} | {pair('Top3_coverage',3)} | {pair('1X2_Brier')} | {pair('RPS')} | {pair('OU_over2_5_Brier')} | {pair('AH_settlement_aware_Brier')} | {item['activation']} |")
    lines += ["", "## Scope", "", "- UCL: `NOT_CALIBRATED_V1`; no Big5 coefficient transfer.", "- A SHADOW artifact is intentionally not loadable by the runtime."]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--out", default="database/research/recent_form_v1")
    parser.add_argument("--docs", default="docs/MODEL_1_RECENT_FORM_V1.md")
    args = parser.parse_args()
    source_sha = file_sha256(args.db)
    if source_sha != RAW_SHA256:
        raise RuntimeError("TITAN_MOTHER_SOURCE_SHA256_MISMATCH")
    raw_rows, audit = load_titan_matches(args.db)
    rows = [row for row in raw_rows if row["league"] in DOMESTIC]
    duplicate_id = len({row["match_id"] for row in rows}) != len(rows)
    natural = {(row["league"], row["match_date"], row["home_team"], row["away_team"]) for row in rows}
    if duplicate_id or len(natural) != len(rows):
        raise RuntimeError("TITAN_DUPLICATE_MATCHES")
    output_root = Path(args.out); output_root.mkdir(parents=True, exist_ok=True)
    archive = TitanMarketArchive(args.db)
    try:
        markets = collect_markets(archive, rows, output_root / "market_cluster_cache.json")
    finally:
        archive.close()
    summary: dict[str, Any] = {"version": CALIBRATION_VERSION, "source": {"sha256": source_sha, "audit": audit, "big5_rows": len(rows), "missing_results": 0, "duplicate_match_id": False, "duplicate_natural_key": False},
                               "splits": SEASONS, "frozen_gate": GATE, "market_definition": "build_market_cluster_likelihood(Pinnacle,Bet365,Macau)", "ucl": "NOT_CALIBRATED_V1", "leagues": {}}
    summary["no_future_leakage"] = {"source_match_kickoff_rule": "source_match_kickoff < target_match_kickoff", "same_kickoff_batched": True}
    for league in DOMESTIC:
        league_rows = [row for row in rows if row["league"] == league]
        candidates: dict[str, dict[str, dict[str, Any]]] = {}
        for spec in FEATURE_GRID:
            key = json.dumps(spec, sort_keys=True)
            matches = [RecentMatch(row["match_id"], row["match_date"], row["league"], row["season_start"], row["home_team"], row["away_team"], row["home_score"], row["away_score"]) for row in league_rows]
            candidates[key] = RecentFormFeatureBuilder(**spec).transform(matches)
        summary["leagues"][league] = {}
        for phase in ("opening", "closing"):
            selected, model = select_train_only(league_rows, candidates, markets, phase)
            feature_rows = candidates[selected["feature_spec"]]
            validation = _records_for(league_rows, feature_rows, markets, phase, SEASONS["validation"])
            test = _records_for(league_rows, feature_rows, markets, phase, SEASONS["test"])
            base_val, base_val_detail = evaluate(validation, None); recent_val, recent_val_detail = evaluate(validation, model)
            base_test, base_test_detail = evaluate(test, None); recent_test, recent_test_detail = evaluate(test, model)
            val_report = {"base": base_val, "recent": recent_val, "bootstrap": paired_bootstrap(base_val_detail, recent_val_detail, seed=20260915),
                          "placebo": evaluate(validation, model, placebo_seed=20260915)[0]}
            test_report = {"base": base_test, "recent": recent_test, "bootstrap": paired_bootstrap(base_test_detail, recent_test_detail, seed=20260916),
                           "placebo": evaluate(test, model, placebo_seed=20260916)[0]}
            validation_pass, validation_reasons = frozen_gate(val_report)
            test_pass, test_reasons = frozen_gate(test_report)
            placebo_delta = test_report["placebo"]["correct_score_NLL"] - base_test["correct_score_NLL"]
            placebo_ok = abs(placebo_delta) <= GATE["placebo_absolute_delta_limit"]
            activation = APPROVED_STATUS if validation_pass and test_pass and placebo_ok else "SHADOW"
            reasons = (["VALIDATION:" + item for item in validation_reasons] + ["TEST:" + item for item in test_reasons] + ([] if placebo_ok else ["PLACEBO_INCREMENT_NOT_DISAPPEARED"]))
            artifact = make_artifact(competition=league, phase=phase, selected=selected, model=model, activation=activation, reasons=reasons, source_sha=source_sha)
            dump(output_root / f"{league}_{phase}.json", artifact)
            summary["leagues"][league][phase] = {"selected_train_only": selected, "validation": val_report, "test": test_report,
                                                     "activation": activation, "activation_reasons": reasons, "placebo_delta_nll": placebo_delta,
                                                     "artifact": str(output_root / f"{league}_{phase}.json")}
            print(league, phase, activation, flush=True)
    dump(output_root / "summary.json", summary)
    Path(args.docs).write_text(render_doc(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
