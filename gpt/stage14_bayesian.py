"""MODEL_1 Stage14 Bayesian-Poisson/Dixon-Coles score engine.

Formal semantics:
- build an independent log-rate prior from league/team inputs;
- treat Pinnacle/Bet365/Macau market reconstructions as one correlated market cluster,
  not three independent votes and not a simple final lambda average;
- apply only validated quantitative context updates;
- integrate over the posterior of log(lambda_home), log(lambda_away) with
  deterministic Monte Carlo to produce a posterior-predictive Dixon-Coles grid;
- keep raw posterior scores separate from final direction-consistent Top3.

This module never issues or changes the formal ticket.
"""
from __future__ import annotations

from hashlib import sha256
from math import isfinite
from typing import Any, Mapping, Sequence

import numpy as np

from gpt.quant_core import correct_score_probabilities, probabilities_1x2, score_grid

ENGINE_VERSION = "MODEL_1-STAGE14-BAYES-1.0.0"
CORE_MARKET_COMPANIES = ("Pinnacle", "Bet365", "Macau")
SOURCE_GROUPS = {
    "TEAM_DATA",
    "LINEUP",
    "1X2",
    "AH",
    "OU_MAIN",
    "OU_CURVE",
    "OFFFIELD",
}


class BayesianScoreError(ValueError):
    pass


def _as_vec2(value: Sequence[float], name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (2,) or not np.all(np.isfinite(arr)):
        raise BayesianScoreError(f"{name} must be a finite length-2 vector.")
    return arr


def _as_cov2(value: Sequence[Sequence[float]], name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.shape != (2, 2) or not np.all(np.isfinite(arr)):
        raise BayesianScoreError(f"{name} must be a finite 2x2 covariance matrix.")
    if not np.allclose(arr, arr.T, atol=1e-10):
        raise BayesianScoreError(f"{name} must be symmetric.")
    eig = np.linalg.eigvalsh(arr)
    if np.min(eig) <= 0:
        raise BayesianScoreError(f"{name} must be positive definite.")
    return arr


def build_log_rate_prior(components: Mapping[str, Any]) -> dict[str, Any]:
    """Build the approved MODEL_1 prior in log-rate space.

    log(lambda_H) = mu_L + HFA_L + Attack_H - Defense_A + X_beta_home
    log(lambda_A) = mu_L + Attack_A - Defense_H + X_beta_away

    Estimation/calibration of the inputs is upstream; this function never invents
    attack, defense, HFA, lineup or contextual numeric effects.
    """
    required = (
        "mu_league",
        "hfa_league",
        "attack_home",
        "defense_away",
        "attack_away",
        "defense_home",
        "cov_log_lambda",
    )
    missing = [key for key in required if key not in components]
    if missing:
        raise BayesianScoreError(f"Prior components missing: {', '.join(missing)}")

    values = {key: float(components[key]) for key in required if key != "cov_log_lambda"}
    if not all(isfinite(v) for v in values.values()):
        raise BayesianScoreError("Prior scalar components must be finite.")

    xh = float(components.get("x_beta_home", 0.0))
    xa = float(components.get("x_beta_away", 0.0))
    mu_h = (
        values["mu_league"]
        + values["hfa_league"]
        + values["attack_home"]
        - values["defense_away"]
        + xh
    )
    mu_a = (
        values["mu_league"]
        + values["attack_away"]
        - values["defense_home"]
        + xa
    )
    cov = _as_cov2(components["cov_log_lambda"], "cov_log_lambda")

    source_groups = list(components.get("source_groups", ["TEAM_DATA"]))
    if not source_groups or any(group not in SOURCE_GROUPS for group in source_groups):
        raise BayesianScoreError("Prior source_groups must use approved MODEL_1 groups.")

    return {
        "status": "VALID",
        "engine_version": ENGINE_VERSION,
        "mean_log_lambda": [float(mu_h), float(mu_a)],
        "cov_log_lambda": cov.tolist(),
        "mean_lambda": [float(np.exp(mu_h)), float(np.exp(mu_a))],
        "source_groups": source_groups,
        "components": {
            "mu_league": values["mu_league"],
            "hfa_league": values["hfa_league"],
            "attack_home": values["attack_home"],
            "defense_away": values["defense_away"],
            "attack_away": values["attack_away"],
            "defense_home": values["defense_home"],
            "x_beta_home": xh,
            "x_beta_away": xa,
        },
        "rho_prior": components.get("rho_prior"),
        "calibration_ref": components.get("calibration_ref"),
    }


def _validated_prior(prior_packet: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    if prior_packet.get("status") != "VALID":
        raise BayesianScoreError("Bayesian prior packet must have status=VALID.")
    mu = _as_vec2(prior_packet.get("mean_log_lambda"), "mean_log_lambda")
    cov = _as_cov2(prior_packet.get("cov_log_lambda"), "cov_log_lambda")
    return mu, cov


def _collect_market_reconstructions(
    quant_packet: Mapping[str, Any],
    companies: Sequence[str] = CORE_MARKET_COMPANIES,
) -> list[dict[str, Any]]:
    reconstruction = quant_packet.get("reconstruction")
    if not isinstance(reconstruction, Mapping):
        return []
    rows: list[dict[str, Any]] = []
    for company in companies:
        raw = reconstruction.get(company)
        if not isinstance(raw, Mapping):
            continue
        try:
            lh = float(raw["lambda_home"])
            la = float(raw["lambda_away"])
            rho = float(raw.get("rho", 0.0))
            residual = float(raw.get("max_abs_residual", 0.0))
        except (KeyError, TypeError, ValueError):
            continue
        if not (lh > 0 and la > 0 and all(isfinite(x) for x in (lh, la, rho, residual))):
            continue
        if not (-0.5 < rho < 0.5):
            continue
        rows.append(
            {
                "company": company,
                "log_lambda": np.log([lh, la]),
                "lambda_home": lh,
                "lambda_away": la,
                "rho": rho,
                "fit_residual": max(0.0, residual),
            }
        )
    return rows


def build_market_cluster_likelihood(
    quant_packet: Mapping[str, Any],
    *,
    companies: Sequence[str] = CORE_MARKET_COMPANIES,
    log_lambda_sigma_floor: float = 0.12,
) -> dict[str, Any]:
    """Compress correlated bookmaker reconstructions into ONE market likelihood.

    The company lambdas are not multiplied as independent evidence. Their log-rate
    center forms one market-cluster observation; cross-company dispersion widens
    the observation covariance. The sigma floor prevents false certainty when the
    three books quote near-identical prices.
    """
    sigma_floor = float(log_lambda_sigma_floor)
    if not (sigma_floor > 0 and isfinite(sigma_floor)):
        raise BayesianScoreError("log_lambda_sigma_floor must be finite and > 0.")

    rows = _collect_market_reconstructions(quant_packet, companies)
    if not rows:
        return {
            "status": "MISSING",
            "reason": "NO_CORE_MARKET_RECONSTRUCTION",
            "companies_requested": list(companies),
        }

    matrix = np.vstack([row["log_lambda"] for row in rows])
    center = matrix.mean(axis=0)
    if len(rows) >= 2:
        between = np.cov(matrix.T, ddof=1)
        if np.asarray(between).shape != (2, 2):
            between = np.zeros((2, 2), dtype=float)
    else:
        between = np.zeros((2, 2), dtype=float)

    residual_inflation = float(np.mean([row["fit_residual"] for row in rows]))
    inflation = 1.0 + min(2.0, 20.0 * residual_inflation)
    floor_cov = np.eye(2) * (sigma_floor * inflation) ** 2
    covariance = np.asarray(between, dtype=float) + floor_cov
    covariance = (covariance + covariance.T) / 2.0
    _as_cov2(covariance, "market_cluster_covariance")

    rho_values = np.asarray([row["rho"] for row in rows], dtype=float)
    return {
        "status": "VALID",
        "method": "CORRELATED_MARKET_CLUSTER_LOG_RATE",
        "companies_used": [row["company"] for row in rows],
        "mean_log_lambda": center.tolist(),
        "cov_log_lambda": covariance.tolist(),
        "mean_lambda": np.exp(center).tolist(),
        "cross_company_dispersion_cov": np.asarray(between, dtype=float).tolist(),
        "sigma_floor": sigma_floor,
        "fit_residual_mean": residual_inflation,
        "rho_market_median": float(np.median(rho_values)),
        "company_observations": [
            {
                "company": row["company"],
                "lambda_home": row["lambda_home"],
                "lambda_away": row["lambda_away"],
                "rho": row["rho"],
                "fit_residual": row["fit_residual"],
            }
            for row in rows
        ],
        "bookmaker_roles": {
            "Pinnacle": "ANCHOR_CONFIRMATION_NOT_SMART_MONEY_BY_DEFAULT",
            "Bet365": "CANDIDATE_REPRICING_LEAD_REQUIRES_REGIME_CHECK",
            "Macau": "WEAK_LEAD_ASIAN_MARKET_CONFIRMATION",
        },
        "not_independent_votes": True,
        "not_simple_final_lambda_average": True,
    }


def _normal_update(
    prior_mu: np.ndarray,
    prior_cov: np.ndarray,
    obs_mu: np.ndarray,
    obs_cov: np.ndarray,
    *,
    effective_fraction: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    frac = float(effective_fraction)
    if not (0.0 <= frac <= 1.0 and isfinite(frac)):
        raise BayesianScoreError("effective_fraction must be in [0,1].")
    if frac == 0.0:
        return prior_mu.copy(), prior_cov.copy()

    prior_precision = np.linalg.inv(prior_cov)
    obs_precision = np.linalg.inv(obs_cov) * frac
    post_cov = np.linalg.inv(prior_precision + obs_precision)
    post_mu = post_cov @ (prior_precision @ prior_mu + obs_precision @ obs_mu)
    return post_mu, (post_cov + post_cov.T) / 2.0


def apply_validated_context_updates(
    mu: np.ndarray,
    cov: np.ndarray,
    updates: Sequence[Mapping[str, Any]] | None,
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    """Apply only quantitative updates with an explicit validated observation model.

    Narrative claims cannot be converted to lambda shifts here. An update must
    provide mean_log_lambda + cov_log_lambda and validated=True.
    """
    applied: list[dict[str, Any]] = []
    for raw in updates or []:
        if not bool(raw.get("validated", False)):
            applied.append(
                {
                    "source_group": raw.get("source_group"),
                    "status": "IGNORED_UNVALIDATED",
                }
            )
            continue
        group = str(raw.get("source_group", ""))
        if group not in SOURCE_GROUPS:
            raise BayesianScoreError(f"Unknown source_group: {group!r}")
        obs_mu = _as_vec2(raw.get("mean_log_lambda"), f"{group}.mean_log_lambda")
        obs_cov = _as_cov2(raw.get("cov_log_lambda"), f"{group}.cov_log_lambda")
        absorbed = float(raw.get("absorbed_fraction", 0.0))
        if not (0.0 <= absorbed <= 1.0):
            raise BayesianScoreError("absorbed_fraction must be in [0,1].")
        effective_fraction = 1.0 - absorbed
        mu, cov = _normal_update(
            mu,
            cov,
            obs_mu,
            obs_cov,
            effective_fraction=effective_fraction,
        )
        applied.append(
            {
                "source_group": group,
                "status": "APPLIED",
                "absorbed_fraction": absorbed,
                "effective_fraction": effective_fraction,
                "evidence_ref": raw.get("evidence_ref"),
            }
        )
    return mu, cov, applied


def build_lambda_posterior(
    quant_packet: Mapping[str, Any],
    prior_packet: Mapping[str, Any],
    *,
    context_updates: Sequence[Mapping[str, Any]] | None = None,
    market_absorbed_fraction: float = 0.0,
    market_sigma_floor: float = 0.12,
) -> dict[str, Any]:
    prior_mu, prior_cov = _validated_prior(prior_packet)
    market = build_market_cluster_likelihood(
        quant_packet,
        log_lambda_sigma_floor=market_sigma_floor,
    )
    if market.get("status") != "VALID":
        return {
            "status": "MISSING",
            "reason": market.get("reason", "MARKET_LIKELIHOOD_MISSING"),
            "prior_packet": dict(prior_packet),
            "market_likelihood": market,
        }

    absorbed = float(market_absorbed_fraction)
    if not (0.0 <= absorbed <= 1.0):
        raise BayesianScoreError("market_absorbed_fraction must be in [0,1].")

    market_mu = _as_vec2(market["mean_log_lambda"], "market.mean_log_lambda")
    market_cov = _as_cov2(market["cov_log_lambda"], "market.cov_log_lambda")
    post_mu, post_cov = _normal_update(
        prior_mu,
        prior_cov,
        market_mu,
        market_cov,
        effective_fraction=1.0 - absorbed,
    )
    post_mu, post_cov, applied = apply_validated_context_updates(
        post_mu,
        post_cov,
        context_updates,
    )

    rho_prior = prior_packet.get("rho_prior")
    if isinstance(rho_prior, Mapping) and rho_prior.get("validated") is True:
        rho = float(rho_prior["mean"])
        rho_source = "VALIDATED_HISTORICAL_PRIOR"
    else:
        rho = float(market["rho_market_median"])
        rho_source = "CORE_MARKET_RECONSTRUCTION_MEDIAN"
    rho = float(np.clip(rho, -0.249, 0.249))

    return {
        "status": "BAYESIAN_POSTERIOR",
        "engine_version": ENGINE_VERSION,
        "mean_log_lambda": post_mu.tolist(),
        "cov_log_lambda": post_cov.tolist(),
        "median_lambda": np.exp(post_mu).tolist(),
        "mean_lambda_lognormal": np.exp(post_mu + 0.5 * np.diag(post_cov)).tolist(),
        "rho": rho,
        "rho_source": rho_source,
        "market_absorbed_fraction": absorbed,
        "prior": {
            "mean_log_lambda": prior_mu.tolist(),
            "cov_log_lambda": prior_cov.tolist(),
            "source_groups": prior_packet.get("source_groups"),
            "calibration_ref": prior_packet.get("calibration_ref"),
        },
        "market_likelihood": market,
        "context_updates": applied,
        "anti_double_counting": True,
    }


def _deterministic_seed(match_id: str | None, engine_version: str = ENGINE_VERSION) -> int:
    raw = f"{engine_version}|{match_id or ''}".encode("utf-8")
    return int.from_bytes(sha256(raw).digest()[:8], "big") % (2**32 - 1)


def posterior_predictive_grid(
    posterior: Mapping[str, Any],
    *,
    match_id: str | None = None,
    max_goals: int = 12,
    draws: int = 4000,
) -> dict[str, Any]:
    if posterior.get("status") != "BAYESIAN_POSTERIOR":
        return {"status": "MISSING", "reason": "VALID_BAYESIAN_POSTERIOR_REQUIRED"}
    if max_goals < 6:
        raise BayesianScoreError("max_goals must be >= 6.")
    if draws < 500:
        raise BayesianScoreError("draws must be >= 500.")

    mu = _as_vec2(posterior["mean_log_lambda"], "posterior.mean_log_lambda")
    cov = _as_cov2(posterior["cov_log_lambda"], "posterior.cov_log_lambda")
    rho = float(posterior["rho"])
    seed = _deterministic_seed(match_id)
    rng = np.random.default_rng(seed)
    samples = rng.multivariate_normal(mu, cov, size=int(draws))

    grid_sum = np.zeros((max_goals + 1, max_goals + 1), dtype=float)
    robustness_counts = np.zeros_like(grid_sum)
    lambda_samples = np.exp(np.clip(samples, np.log(0.05), np.log(6.0)))

    for lh, la in lambda_samples:
        grid = score_grid(float(lh), float(la), rho, max_goals=max_goals)
        grid_sum += grid
        flat = grid.ravel()
        top3_idx = np.argpartition(flat, -3)[-3:]
        robustness_counts.ravel()[top3_idx] += 1.0

    predictive = grid_sum / float(draws)
    predictive = predictive / predictive.sum()
    robustness = robustness_counts / float(draws)
    top10 = correct_score_probabilities(predictive, 10)
    for row in top10:
        h, a = (int(x) for x in row["score"].split("-"))
        row["robustness_top3_frequency"] = float(robustness[h, a])

    return {
        "status": "BAYESIAN_POSTERIOR_PREDICTIVE",
        "engine_version": ENGINE_VERSION,
        "draws": int(draws),
        "seed": int(seed),
        "rho": rho,
        "posterior_mean_lambda": [
            float(lambda_samples[:, 0].mean()),
            float(lambda_samples[:, 1].mean()),
        ],
        "posterior_sd_lambda": [
            float(lambda_samples[:, 0].std(ddof=1)),
            float(lambda_samples[:, 1].std(ddof=1)),
        ],
        "model_1x2": probabilities_1x2(predictive),
        "top10": top10,
        "grid": predictive.tolist(),
        "robustness_top3_frequency_grid": robustness.tolist(),
        "five_plus_home_tail": float(predictive[5:, :].sum()),
        "five_plus_away_tail": float(predictive[:, 5:].sum()),
        "any_team_five_plus_tail": float(
            predictive[5:, :].sum()
            + predictive[:, 5:].sum()
            - predictive[5:, 5:].sum()
        ),
    }


def _split_quarter(line: float) -> tuple[float, float]:
    q = round(float(line) * 4.0) / 4.0
    if abs(q - float(line)) > 1e-8:
        raise BayesianScoreError("Asian line must be a quarter-goal increment.")
    n = int(round(q * 4.0))
    if n % 2 == 0:
        return q, q
    return (n - 1) / 4.0, (n + 1) / 4.0


def _single_score_ah_payoff(home_goals: int, away_goals: int, home_handicap: float) -> float:
    l1, l2 = _split_quarter(home_handicap)
    margin = home_goals - away_goals

    def leg(line: float) -> int:
        value = margin + line
        return 1 if value > 1e-10 else (-1 if value < -1e-10 else 0)

    return (leg(l1) + leg(l2)) / 2.0


def _score_direction_flags(score: str, execution_path: Mapping[str, Any] | None) -> dict[str, Any]:
    h, a = (int(x) for x in score.split("-"))
    path = dict(execution_path or {})
    winner = path.get("winner")
    winner_ok = True
    if winner == "HOME":
        winner_ok = h > a
    elif winner == "AWAY":
        winner_ok = a > h
    elif winner == "DRAW":
        winner_ok = h == a

    ah_ok = True
    ah_payoff = None
    ah = path.get("ah")
    if isinstance(ah, Mapping) and bool(ah.get("hard_gate", False)):
        home_handicap = float(ah["home_handicap"])
        payoff_home = _single_score_ah_payoff(h, a, home_handicap)
        backing = str(ah.get("backing", "HOME")).upper()
        ah_payoff = payoff_home if backing == "HOME" else -payoff_home
        ah_ok = ah_payoff > 0.0

    ou_ok = True
    ou_relation = None
    ou = path.get("ou")
    if isinstance(ou, Mapping):
        line = float(ou["line"])
        side = str(ou.get("side", "")).upper()
        total = h + a
        if side == "OVER":
            ou_relation = total - line
            ou_ok = total > line if bool(ou.get("hard_gate", False)) else total >= line
        elif side == "UNDER":
            ou_relation = line - total
            ou_ok = total < line if bool(ou.get("hard_gate", False)) else total <= line

    return {
        "winner_ok": bool(winner_ok),
        "ah_ok": bool(ah_ok),
        "ou_ok": bool(ou_ok),
        "ah_payoff": ah_payoff,
        "ou_relation": ou_relation,
        "hard_direction_ok": bool(winner_ok and ah_ok),
    }


def select_direction_consistent_top3(
    predictive: Mapping[str, Any],
    *,
    execution_path: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if predictive.get("status") != "BAYESIAN_POSTERIOR_PREDICTIVE":
        return {"status": "MISSING", "reason": "POSTERIOR_PREDICTIVE_REQUIRED", "top3": []}

    rows = []
    for raw in predictive.get("top10", []):
        row = dict(raw)
        row.update(_score_direction_flags(row["score"], execution_path))
        rows.append(row)

    eligible = [row for row in rows if row["hard_direction_ok"]]
    ou_preferred = [row for row in eligible if row.get("ou_ok", True)]
    ou_fallback = [row for row in eligible if not row.get("ou_ok", True)]
    for group in (ou_preferred, ou_fallback):
        group.sort(
            key=lambda row: (
                float(row["probability"]),
                float(row.get("robustness_top3_frequency", 0.0)),
            ),
            reverse=True,
        )
    top3 = (ou_preferred + ou_fallback)[:3]
    status = "BAYESIAN_POSTERIOR_TOP3" if top3 else "SCORELINE_CONFLICT"
    return {
        "status": status,
        "top3": top3,
        "raw_top10": rows,
        "execution_path": dict(execution_path or {}),
        "ou_is_auxiliary": True,
        "ranking_policy": (
            "HARD_1X2_AH_DIRECTION_GATE_THEN_AUXILIARY_OU_CONSISTENCY_"
            "THEN_POSTERIOR_PROBABILITY_AND_ROBUSTNESS"
        ),
    }


def build_stage14_score_packet(
    quant_packet: Mapping[str, Any],
    prior_packet: Mapping[str, Any],
    *,
    context_updates: Sequence[Mapping[str, Any]] | None = None,
    execution_path: Mapping[str, Any] | None = None,
    market_absorbed_fraction: float = 0.0,
    market_sigma_floor: float = 0.12,
    max_goals: int = 12,
    draws: int = 4000,
) -> dict[str, Any]:
    match_id = str(quant_packet.get("match_id", ""))
    posterior = build_lambda_posterior(
        quant_packet,
        prior_packet,
        context_updates=context_updates,
        market_absorbed_fraction=market_absorbed_fraction,
        market_sigma_floor=market_sigma_floor,
    )
    if posterior.get("status") != "BAYESIAN_POSTERIOR":
        return {
            "status": "MISSING",
            "reason": posterior.get("reason", "POSTERIOR_BUILD_FAILED"),
            "posterior": posterior,
            "top3": [],
        }
    predictive = posterior_predictive_grid(
        posterior,
        match_id=match_id,
        max_goals=max_goals,
        draws=draws,
    )
    selected = select_direction_consistent_top3(predictive, execution_path=execution_path)
    return {
        "status": selected["status"],
        "engine_version": ENGINE_VERSION,
        "match_id": match_id,
        "provenance": "BAYESIAN_POSTERIOR_POISSON_DIXON_COLES",
        "posterior": posterior,
        "posterior_predictive": predictive,
        "top3": selected["top3"],
        "raw_top10": selected["raw_top10"],
        "execution_path": selected["execution_path"],
        "ranking_policy": selected["ranking_policy"],
        "market_reconstruction_role": "LIKELIHOOD_OR_MARKET_REFERENCE_ONLY",
        "no_market_only_fallback": True,
    }
