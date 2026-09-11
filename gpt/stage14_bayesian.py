from __future__ import annotations

from datetime import datetime
from math import exp, isfinite, log
from typing import Any, Mapping, Sequence

import numpy as np

from gpt.quant_core import (
    correct_score_probabilities,
    probabilities_1x2,
    score_grid,
    total_settlement,
    win_equivalent_probability,
)

POSTERIOR_ENGINE_VERSION = "MODEL_1-BAYES-SCORE-1.0.0"


class BayesianScoreInputError(ValueError):
    pass


def _as_time(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise BayesianScoreInputError(f"Invalid evidence timestamp: {value!r}") from exc


def _validate_particle(row: Mapping[str, Any]) -> tuple[float, float, float, float]:
    lh = float(row["lambda_home"])
    la = float(row["lambda_away"])
    rho = float(row.get("rho", 0.0))
    weight = float(row.get("weight", row.get("prior_weight", 1.0)))
    if not (isfinite(lh) and isfinite(la) and lh > 0 and la > 0):
        raise BayesianScoreInputError("Posterior/prior lambdas must be finite and > 0.")
    if not (isfinite(rho) and -0.5 < rho < 0.5):
        raise BayesianScoreInputError("rho must lie in (-0.5, 0.5).")
    if not (isfinite(weight) and weight >= 0):
        raise BayesianScoreInputError("Particle weight must be finite and >= 0.")
    return lh, la, rho, weight


def _normalized_particles(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, float]]:
    if len(rows) < 2:
        raise BayesianScoreInputError("A Bayesian distribution requires at least two particles.")
    parsed: list[dict[str, float]] = []
    for row in rows:
        lh, la, rho, weight = _validate_particle(row)
        parsed.append({"lambda_home": lh, "lambda_away": la, "rho": rho, "weight": weight})
    total = sum(r["weight"] for r in parsed)
    if total <= 0:
        raise BayesianScoreInputError("Particle weights have zero total mass.")
    for row in parsed:
        row["weight"] /= total
    return parsed


def _gaussian_log_kernel(value: float, target: float, sigma: float) -> float:
    if not (isfinite(sigma) and sigma > 0):
        raise BayesianScoreInputError("Evidence sigma must be finite and > 0; no default sigma is invented.")
    z = (value - target) / sigma
    return -0.5 * z * z


def _market_log_likelihood(particle: Mapping[str, float], evidence: Mapping[str, Any]) -> float:
    target = evidence.get("target_1x2")
    if not isinstance(target, Mapping):
        raise BayesianScoreInputError("market_1x2_ou evidence requires target_1x2.")
    th, td, ta = (float(target[k]) for k in ("home", "draw", "away"))
    if abs((th + td + ta) - 1.0) > 1e-6:
        raise BayesianScoreInputError("target_1x2 must sum to one.")
    line = float(evidence["ou_line"])
    target_over = float(evidence["target_over_probability"])
    grid = score_grid(particle["lambda_home"], particle["lambda_away"], particle["rho"])
    p = probabilities_1x2(grid)
    over_equiv = win_equivalent_probability(total_settlement(grid, line, "over"))
    return (
        _gaussian_log_kernel(p["home"], th, float(evidence["sigma_home"]))
        + _gaussian_log_kernel(p["draw"], td, float(evidence["sigma_draw"]))
        + _gaussian_log_kernel(over_equiv, target_over, float(evidence["sigma_over"]))
    )


def _context_log_likelihood(particle: Mapping[str, float], evidence: Mapping[str, Any]) -> float:
    total = 0.0
    if "target_log_lambda_home" in evidence:
        total += _gaussian_log_kernel(
            log(particle["lambda_home"]),
            float(evidence["target_log_lambda_home"]),
            float(evidence["sigma_log_lambda_home"]),
        )
    if "target_log_lambda_away" in evidence:
        total += _gaussian_log_kernel(
            log(particle["lambda_away"]),
            float(evidence["target_log_lambda_away"]),
            float(evidence["sigma_log_lambda_away"]),
        )
    if "target_rho" in evidence:
        total += _gaussian_log_kernel(
            particle["rho"],
            float(evidence["target_rho"]),
            float(evidence["sigma_rho"]),
        )
    if total == 0.0 and not any(k in evidence for k in ("target_log_lambda_home", "target_log_lambda_away", "target_rho")):
        raise BayesianScoreInputError("context_lambda evidence contains no statistical target.")
    return total


def build_bayesian_posterior(
    *,
    prior_particles: Sequence[Mapping[str, Any]],
    evidence_records: Sequence[Mapping[str, Any]],
    prior_provenance: Mapping[str, Any],
    cutoff_time: Any = None,
) -> dict[str, Any]:
    """Bayesian particle reweighting for MODEL_1 Stage14.

    No prior strength, evidence weight or uncertainty is invented here. Every
    likelihood width must be supplied by validated/calibrated upstream evidence.
    """
    particles = _normalized_particles(prior_particles)
    if not prior_provenance:
        raise BayesianScoreInputError("prior_provenance is required.")
    cutoff = _as_time(cutoff_time)
    accepted: list[Mapping[str, Any]] = []
    log_weights = np.array([log(max(p["weight"], 1e-300)) for p in particles], dtype=float)

    for evidence in evidence_records:
        if evidence.get("validated_for_update") is not True:
            continue
        if evidence.get("independent_update") is not True:
            continue
        timestamp = _as_time(evidence.get("timestamp"))
        if cutoff is not None and timestamp is not None and timestamp > cutoff:
            continue
        kind = str(evidence.get("kind", ""))
        if kind == "market_1x2_ou":
            fn = _market_log_likelihood
        elif kind == "context_lambda":
            fn = _context_log_likelihood
        else:
            continue
        for i, particle in enumerate(particles):
            log_weights[i] += fn(particle, evidence)
        accepted.append(evidence)

    if not accepted:
        return {
            "engine_version": POSTERIOR_ENGINE_VERSION,
            "status": "PRIOR_ONLY",
            "formal_stage14_usable": False,
            "reason": "NO_VALIDATED_INDEPENDENT_EVIDENCE",
            "prior_provenance": dict(prior_provenance),
            "posterior_particles": particles,
            "accepted_evidence_count": 0,
        }

    log_weights -= float(np.max(log_weights))
    weights = np.exp(log_weights)
    weight_sum = float(weights.sum())
    if not isfinite(weight_sum) or weight_sum <= 0:
        raise BayesianScoreInputError("Posterior normalization failed.")
    weights /= weight_sum
    posterior = []
    for particle, weight in zip(particles, weights):
        posterior.append({
            "lambda_home": particle["lambda_home"],
            "lambda_away": particle["lambda_away"],
            "rho": particle["rho"],
            "weight": float(weight),
        })
    return {
        "engine_version": POSTERIOR_ENGINE_VERSION,
        "status": "POSTERIOR_VALIDATED",
        "formal_stage14_usable": True,
        "prior_provenance": dict(prior_provenance),
        "accepted_evidence_count": len(accepted),
        "accepted_evidence_ids": [str(e.get("evidence_id", "")) for e in accepted],
        "posterior_particles": posterior,
    }


def posterior_predictive_grid(posterior_packet: Mapping[str, Any], max_goals: int = 12) -> np.ndarray:
    if posterior_packet.get("status") != "POSTERIOR_VALIDATED":
        raise BayesianScoreInputError("Formal Stage14 requires status=POSTERIOR_VALIDATED.")
    rows = posterior_packet.get("posterior_particles")
    if not isinstance(rows, Sequence):
        raise BayesianScoreInputError("posterior_particles are required.")
    particles = _normalized_particles(rows)
    grid = np.zeros((max_goals + 1, max_goals + 1), dtype=float)
    for particle in particles:
        grid += particle["weight"] * score_grid(
            particle["lambda_home"],
            particle["lambda_away"],
            particle["rho"],
            max_goals=max_goals,
        )
    mass = float(grid.sum())
    if mass <= 0 or not isfinite(mass):
        raise BayesianScoreInputError("Posterior predictive grid has invalid mass.")
    return grid / mass


def posterior_score_summary(posterior_packet: Mapping[str, Any], max_goals: int = 12) -> dict[str, Any]:
    grid = posterior_predictive_grid(posterior_packet, max_goals=max_goals)
    rows = _normalized_particles(posterior_packet["posterior_particles"])
    mean_lh = sum(p["weight"] * p["lambda_home"] for p in rows)
    mean_la = sum(p["weight"] * p["lambda_away"] for p in rows)
    mean_rho = sum(p["weight"] * p["rho"] for p in rows)
    top10 = correct_score_probabilities(grid, 10)
    return {
        "status": "BAYESIAN_POSTERIOR_POISSON_DC",
        "engine_version": POSTERIOR_ENGINE_VERSION,
        "posterior_lambda_home_mean": mean_lh,
        "posterior_lambda_away_mean": mean_la,
        "posterior_rho_mean": mean_rho,
        "posterior_1x2": probabilities_1x2(grid),
        "top3": top10[:3],
        "top10": top10,
        "five_plus_home_tail": float(grid[5:, :].sum()),
        "five_plus_away_tail": float(grid[:, 5:].sum()),
        "any_team_five_plus_tail": float(grid[5:, :].sum() + grid[:, 5:].sum() - grid[5:, 5:].sum()),
    }
