from __future__ import annotations

from typing import Any, Mapping, Sequence

from gpt.quant_core import score_grid, correct_score_probabilities
from gpt.stage14_bayesian import build_stage14_score_packet


def market_reconstruction_top3(quant_packet: Mapping[str, Any], company: str) -> dict[str, Any]:
    """Legacy/research-only market reconstruction view.

    This is never the formal MODEL_1 Stage14 output after the Bayesian engine repair.
    """
    reconstruction = quant_packet.get("reconstruction", {})
    if company not in reconstruction:
        return {"status": "MISSING", "reason": "NO_RECONSTRUCTION", "top3": []}
    rec = reconstruction[company]
    grid = score_grid(float(rec["lambda_home"]), float(rec["lambda_away"]), float(rec["rho"]))
    rows = correct_score_probabilities(grid, 10)
    return {
        "status": "MARKET_RECONSTRUCTION_RESEARCH_ONLY",
        "top3": rows[:3],
        "top10": rows,
        "formal_stage14": False,
    }


def _formal_execution_path(execution_path: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    """Enforce MODEL_1's formal AH scoreline gate on Stage14 output.

    If a formal AH path is supplied, every displayed scoreline must settle the
    selected AH side positively (> 0 payoff). Push/half-loss/full-loss scorelines
    are therefore ineligible. The underlying posterior distribution is untouched.
    """
    if execution_path is None:
        return None
    path = dict(execution_path)
    ah = path.get("ah")
    if isinstance(ah, Mapping):
        ah_path = dict(ah)
        if bool(ah_path.get("formal", True)):
            ah_path["hard_gate"] = True
            ah_path["positive_settlement_required"] = True
            ah_path["push_allowed"] = False
        path["ah"] = ah_path
    return path


def automatic_top3(
    quant_packet: Mapping[str, Any],
    company: str | None = None,
    *,
    prior_packet: Mapping[str, Any] | None = None,
    context_updates: Sequence[Mapping[str, Any]] | None = None,
    execution_path: Mapping[str, Any] | None = None,
    market_absorbed_fraction: float = 0.0,
    market_sigma_floor: float = 0.12,
    max_goals: int = 12,
    draws: int = 4000,
) -> dict[str, Any]:
    """Formal MODEL_1 automatic Stage14 entry point.

    A validated Bayesian prior is mandatory. `company` is accepted only for backward
    call compatibility and is not used to select a single bookmaker for the formal
    posterior. Pinnacle/Bet365/Macau are fused as one correlated market cluster.
    """
    if prior_packet is None:
        return {
            "status": "MISSING",
            "reason": "BAYESIAN_PRIOR_REQUIRED",
            "top3": [],
            "no_market_only_fallback": True,
        }
    return build_stage14_score_packet(
        quant_packet,
        prior_packet,
        context_updates=context_updates,
        execution_path=_formal_execution_path(execution_path),
        market_absorbed_fraction=market_absorbed_fraction,
        market_sigma_floor=market_sigma_floor,
        max_goals=max_goals,
        draws=draws,
    )
