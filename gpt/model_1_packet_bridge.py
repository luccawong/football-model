"""MODEL_1 packet bridge.

Maps validated Quant/Feature outputs into the 18-stage formal trace without
changing the underlying mathematical engines. Formal Stage14 now requires the
MODEL_1 Bayesian posterior score engine; market reconstruction alone is research-only.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from gpt.feature_engine import module_gate
from gpt.stage14_bayesian import build_stage14_score_packet

PACKET_BRIDGE_VERSION = "MODEL_1-PACKET-BRIDGE-1.1.0"


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
    prior_packet: Mapping[str, Any] | None = None,
    context_updates: Sequence[Mapping[str, Any]] | None = None,
    execution_path: Mapping[str, Any] | None = None,
    market_absorbed_fraction: float = 0.0,
    market_sigma_floor: float = 0.12,
    max_goals: int = 12,
    draws: int = 4000,
    # Legacy arguments are retained only so old callers fail clearly instead of
    # silently producing a market-only score packet.
    company: str | None = None,
    bayesian_context_update: Mapping[str, Any] | None = None,
    final_top3: Sequence[str] | None = None,
    direction_consistency_gate: bool | None = None,
) -> dict[str, Any]:
    """Build formal MODEL_1 Stage14 evidence from a true Bayesian posterior.

    A validated prior is mandatory. Pinnacle/Bet365/Macau reconstructions are
    consumed jointly by the posterior engine as a correlated market cluster.
    The bridge never promotes single-company market reconstruction to formal Top3.
    """
    if prior_packet is None:
        raise PacketBridgeError(
            "Formal MODEL_1 Stage14 requires prior_packet; market-only fallback is forbidden."
        )

    stage14 = build_stage14_score_packet(
        quant_packet,
        prior_packet,
        context_updates=context_updates,
        execution_path=execution_path,
        market_absorbed_fraction=market_absorbed_fraction,
        market_sigma_floor=market_sigma_floor,
        max_goals=max_goals,
        draws=draws,
    )
    if stage14.get("status") not in {"BAYESIAN_POSTERIOR_TOP3", "SCORELINE_CONFLICT"}:
        raise PacketBridgeError(
            f"Formal Stage14 unavailable: {stage14.get('reason', stage14.get('status'))}"
        )

    predictive = stage14.get("posterior_predictive", {})
    top3_rows = list(stage14.get("top3", []))
    return {
        "packet_bridge_version": PACKET_BRIDGE_VERSION,
        "model_id": "MODEL_1",
        "formal_stage": "correct_score_poisson_dixon_coles_bayesian",
        "quant_engine_version": quant_packet.get("engine_version"),
        "stage14_engine_version": stage14.get("engine_version"),
        "quant_packet_ref": {
            "match_id": quant_packet.get("match_id"),
            "snapshot_time": quant_packet.get("snapshot_time"),
            "companies": ["Pinnacle", "Bet365", "Macau"],
        },
        "posterior_ref": {
            "status": stage14.get("posterior", {}).get("status"),
            "mean_log_lambda": stage14.get("posterior", {}).get("mean_log_lambda"),
            "cov_log_lambda": stage14.get("posterior", {}).get("cov_log_lambda"),
            "rho": stage14.get("posterior", {}).get("rho"),
            "rho_source": stage14.get("posterior", {}).get("rho_source"),
        },
        "score_grid_ref": {
            "provenance": stage14.get("provenance"),
            "model_1x2": predictive.get("model_1x2"),
            "raw_top10": stage14.get("raw_top10"),
            "five_plus_home_tail": predictive.get("five_plus_home_tail"),
            "five_plus_away_tail": predictive.get("five_plus_away_tail"),
            "any_team_five_plus_tail": predictive.get("any_team_five_plus_tail"),
        },
        "top3_scores": [row.get("score") for row in top3_rows],
        "top3_rows": top3_rows,
        "direction_consistency_gate": stage14.get("status") != "SCORELINE_CONFLICT",
        "execution_path": stage14.get("execution_path"),
        "market_reconstruction_role": "LIKELIHOOD_OR_MARKET_REFERENCE_ONLY",
        "no_market_only_fallback": True,
        "legacy_manual_top3_ignored": final_top3 is not None,
        "legacy_single_company_ignored": company is not None,
        "legacy_context_blob_preserved_only": dict(bayesian_context_update or {}),
        "legacy_direction_flag_preserved_only": direction_consistency_gate,
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
