from __future__ import annotations

from typing import Any, Mapping

from gpt.quant_core import correct_score_probabilities, score_grid
from gpt.stage14_bayesian import BayesianScoreInputError, posterior_score_summary


def _market_preview(quant_packet: Mapping[str, Any], company: str) -> dict[str, Any]:
    reconstruction = quant_packet.get("reconstruction", {})
    if company not in reconstruction:
        return {"status": "MISSING", "reason": "NO_RECONSTRUCTION", "top3": []}
    rec = reconstruction[company]
    grid = score_grid(float(rec["lambda_home"]), float(rec["lambda_away"]), float(rec["rho"]))
    rows = correct_score_probabilities(grid, 10)
    return {
        "status": "MARKET_RECONSTRUCTION_PREVIEW_ONLY",
        "formal_stage14_usable": False,
        "top3": rows[:3],
        "top10": rows,
    }


def automatic_top3(
    quant_packet: Mapping[str, Any],
    company: str,
    bayesian_posterior_packet: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return formal MODEL_1 Stage14 Top3 only from a validated posterior.

    Market reconstruction remains visible as diagnostic evidence but is never
    silently promoted to the formal correct-score output.
    """
    preview = _market_preview(quant_packet, company)
    if bayesian_posterior_packet is None:
        return {
            "status": "INSUFFICIENT_SOURCE_DATA",
            "formal_stage14_usable": False,
            "reason": "BAYESIAN_POSTERIOR_REQUIRED",
            "market_preview": preview,
            "top3": [],
        }
    try:
        summary = posterior_score_summary(bayesian_posterior_packet)
    except BayesianScoreInputError as exc:
        return {
            "status": "INSUFFICIENT_SOURCE_DATA",
            "formal_stage14_usable": False,
            "reason": str(exc),
            "market_preview": preview,
            "top3": [],
        }
    return {
        **summary,
        "formal_stage14_usable": True,
        "market_preview": preview,
        "source_label": "BAYESIAN_POSTERIOR_POISSON_DC",
    }
