"""MODEL_1 packet bridge.

Keeps the validated mathematical/feature engines independent while mapping their
outputs into the 18-stage MODEL_1 formal trace. This file is orchestration only;
it does not change de-vig, Poisson/Dixon-Coles, AH settlement or uncertainty math.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from gpt.feature_engine import module_gate
from gpt.quant_core import score_grid, probabilities_1x2, correct_score_probabilities

PACKET_BRIDGE_VERSION = "MODEL_1-PACKET-BRIDGE-1.0.0"


class PacketBridgeError(ValueError):
    pass


def build_feature_packet(
    *,
    match_id: str,
    module_records: Mapping[str, Mapping[str, Any]],
    stage_status: Mapping[str, str],
    missing_core_timelines: Sequence[str] | None = None,
    source_conflicts: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Create the MODEL_1 feature/QC packet without inventing missing evidence."""
    gate = module_gate(module_records)
    return {
        "packet_bridge_version": PACKET_BRIDGE_VERSION,
        "model_id": "MODEL_1",
        "formal_stage_refs": [
            "fundamentals",
            "market_snapshot",
            "opening_rationality_lifecycle",
            "off_field_weather",
            "lineup_tactics",
            "uncertainty_audit",
        ],
        "match_id": str(match_id),
        "module_gate": gate,
        "stage_status": dict(stage_status),
        "missing_core_timelines": list(missing_core_timelines or []),
        "source_conflicts": list(source_conflicts or []),
        "missing_is_negative_evidence": False,
    }


def build_correct_score_quant_evidence(
    *,
    quant_packet: Mapping[str, Any],
    company: str,
    bayesian_context_update: Mapping[str, Any],
    final_top3: Sequence[str],
    direction_consistency_gate: bool,
    max_goals: int = 12,
) -> dict[str, Any]:
    """Map one company reconstruction into stage-14 score evidence.

    The Bayesian/context update is supplied explicitly by the formal analysis layer;
    this bridge never fabricates it from the market reconstruction.
    """
    reconstruction = quant_packet.get("reconstruction")
    if not isinstance(reconstruction, Mapping) or company not in reconstruction:
        raise PacketBridgeError(f"No reconstruction available for company {company!r}.")
    rec = reconstruction[company]
    for key in ("lambda_home", "lambda_away", "rho"):
        if key not in rec:
            raise PacketBridgeError(f"Reconstruction missing {key}.")

    grid = score_grid(
        float(rec["lambda_home"]),
        float(rec["lambda_away"]),
        float(rec["rho"]),
        max_goals=max_goals,
    )
    p1x2 = probabilities_1x2(grid)
    top_model_scores = correct_score_probabilities(grid, 10)

    five_plus_home = float(grid[5:, :].sum()) if grid.shape[0] > 5 else 0.0
    five_plus_away = float(grid[:, 5:].sum()) if grid.shape[1] > 5 else 0.0
    any_team_five_plus = float(
        grid[5:, :].sum() + grid[:, 5:].sum() - grid[5:, 5:].sum()
    ) if grid.shape[0] > 5 and grid.shape[1] > 5 else 0.0

    if len(final_top3) > 3:
        raise PacketBridgeError("MODEL_1 final correct-score output is capped at Top3.")

    return {
        "packet_bridge_version": PACKET_BRIDGE_VERSION,
        "model_id": "MODEL_1",
        "formal_stage": "correct_score_poisson_bayesian",
        "quant_engine_version": quant_packet.get("engine_version"),
        "quant_packet_ref": {
            "match_id": quant_packet.get("match_id"),
            "snapshot_time": quant_packet.get("snapshot_time"),
            "company": company,
        },
        "score_grid_ref": {
            "lambda_home": float(rec["lambda_home"]),
            "lambda_away": float(rec["lambda_away"]),
            "rho": float(rec["rho"]),
            "model_1x2": p1x2,
            "raw_top10": top_model_scores,
            "five_plus_home_tail": five_plus_home,
            "five_plus_away_tail": five_plus_away,
            "any_team_five_plus_tail": any_team_five_plus,
        },
        "bayesian_context_update": dict(bayesian_context_update),
        "top3_scores": list(final_top3),
        "direction_consistency_gate": bool(direction_consistency_gate),
    }


def build_runtime_packet(
    *,
    match_id: str,
    quant_packet: Mapping[str, Any] | None,
    feature_packet: Mapping[str, Any] | None,
    formal_trace: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Bundle formal packet references while preserving explicit MISSING states."""
    return {
        "packet_bridge_version": PACKET_BRIDGE_VERSION,
        "model_id": "MODEL_1",
        "match_id": str(match_id),
        "quant_packet": dict(quant_packet) if quant_packet is not None else {"status": "MISSING"},
        "feature_packet": dict(feature_packet) if feature_packet is not None else {"status": "MISSING"},
        "formal_trace": dict(formal_trace) if formal_trace is not None else {"status": "MISSING"},
        "no_silent_substitution": True,
    }
