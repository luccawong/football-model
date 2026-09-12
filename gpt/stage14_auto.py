from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from gpt.prior_engine import PriorEngineError, build_prior_packet
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

    This preserves the main-branch rule added after the prior-engine branch was
    cut: if a formal AH path is supplied, every displayed scoreline must settle
    the selected AH side positively.  The posterior distribution itself remains
    untouched; only the final scoreline eligibility gate is tightened.
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
    prior_context: Mapping[str, Any] | None = None,
    prior_store: Mapping[str, Any] | str | Path | None = None,
    context_updates: Sequence[Mapping[str, Any]] | None = None,
    execution_path: Mapping[str, Any] | None = None,
    market_absorbed_fraction: float = 0.0,
    market_sigma_floor: float = 0.12,
    max_goals: int = 12,
    draws: int = 4000,
) -> dict[str, Any]:
    """Formal MODEL_1 automatic Stage14 entry point.

    A validated Bayesian prior is mandatory.  Callers may still pass a pre-built
    ``prior_packet``.  Alternatively ``prior_context`` + a calibrated Titan
    ``prior_store`` resolve the packet automatically.  The resolver reads only
    league/season/team metadata and historical prior state; it never reads the
    market reconstruction as prior evidence.

    ``company`` is accepted only for backward call compatibility and is not used
    to select a single bookmaker for the formal posterior. Pinnacle/Bet365/Macau
    are fused later as one correlated market likelihood cluster.
    """
    resolution = "EXPLICIT_PRIOR_PACKET"
    if prior_packet is None and prior_store is not None:
        context = prior_context
        if context is None:
            embedded = quant_packet.get("prior_context") or quant_packet.get("match_context")
            context = embedded if isinstance(embedded, Mapping) else None
        if context is None:
            return {
                "status": "MISSING",
                "reason": "BAYESIAN_PRIOR_CONTEXT_REQUIRED",
                "top3": [],
                "no_market_only_fallback": True,
            }
        try:
            prior_packet = build_prior_packet(context, prior_store)
            resolution = "AUTO_TITAN_HISTORICAL_PRIOR"
        except PriorEngineError as exc:
            return {
                "status": "MISSING",
                "reason": "BAYESIAN_PRIOR_UNAVAILABLE",
                "detail": str(exc),
                "top3": [],
                "no_market_only_fallback": True,
            }

    if prior_packet is None:
        return {
            "status": "MISSING",
            "reason": "BAYESIAN_PRIOR_REQUIRED",
            "top3": [],
            "no_market_only_fallback": True,
        }
    out = build_stage14_score_packet(
        quant_packet,
        prior_packet,
        context_updates=context_updates,
        execution_path=_formal_execution_path(execution_path),
        market_absorbed_fraction=market_absorbed_fraction,
        market_sigma_floor=market_sigma_floor,
        max_goals=max_goals,
        draws=draws,
    )
    out["prior_resolution"] = resolution
    return out
