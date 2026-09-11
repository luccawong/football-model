"""MODEL_1 packet bridge.

Keeps the validated mathematical/feature engines independent while mapping their
outputs into the 18-stage MODEL_1 formal trace. This file is orchestration only;
it does not change de-vig, AH settlement or uncertainty math.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from gpt.feature_engine import module_gate
from gpt.quant_core import correct_score_probabilities, probabilities_1x2
from gpt.stage14_bayesian import BayesianScoreInputError, posterior_predictive_grid, posterior_score_summary

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


def _score_probability(grid, score: str) -> float:
    try:
        h_text, a_text = score.replace(":", "-").split("-", 1)
        h, a = int(h_text), int(a_text)
    except (ValueError, AttributeError) as exc:
        raise PacketBridgeError(f"Invalid scoreline {score!r}.") from exc
    if h < 0 or a < 0 or h >= grid.shape[0] or a >= grid.shape[1]:
        raise PacketBridgeError(f"Scoreline {score!r} is outside the configured score grid.")
    return float(grid[h, a])


def build_correct_score_quant_evidence(
    *,
    quant_packet: Mapping[str, Any],
    company: str,
    bayesian_posterior_packet: Mapping[str, Any],
    final_top3: Sequence[str] | None = None,
    direction_consistency_gate: bool,
    max_goals: int = 12,
) -> dict[str, Any]:
    """Build formal MODEL_1 Stage14 evidence from a validated Bayesian posterior.

    Titan market reconstruction remains an evidence/reference packet only. The
    formal score grid is the posterior predictive mixture over lambda/rho states.
    No market-only fallback is allowed here.
    """
    reconstruction = quant_packet.get("reconstruction")
    if not isinstance(reconstruction, Mapping) or company not in reconstruction:
        raise PacketBridgeError(f"No reconstruction available for company {company!r}.")
    rec = reconstruction[company]
    for key in ("lambda_home", "lambda_away", "rho"):
        if key not in rec:
            raise PacketBridgeError(f"Reconstruction missing {key}.")

    try:
        grid = posterior_predictive_grid(bayesian_posterior_packet, max_goals=max_goals)
        summary = posterior_score_summary(bayesian_posterior_packet, max_goals=max_goals)
    except BayesianScoreInputError as exc:
        raise PacketBridgeError(str(exc)) from exc

    raw_top10 = correct_score_probabilities(grid, 10)
    if final_top3 is None:
        selected = [row["score"] for row in raw_top10[:3]]
    else:
        if len(final_top3) > 3:
            raise PacketBridgeError("MODEL_1 final correct-score output is capped at Top3.")
        selected = [str(x).replace(":", "-") for x in final_top3]

    selected_with_probability = [
        {"score": score, "posterior_probability": _score_probability(grid, score)}
        for score in selected
    ]

    return {
        "packet_bridge_version": PACKET_BRIDGE_VERSION,
        "model_id": "MODEL_1",
        "formal_stage": "correct_score_poisson_dixon_coles_bayesian_posterior",
        "formal_stage14_source": "BAYESIAN_POSTERIOR_POISSON_DC",
        "quant_engine_version": quant_packet.get("engine_version"),
        "quant_packet_ref": {
            "match_id": quant_packet.get("match_id"),
            "snapshot_time": quant_packet.get("snapshot_time"),
            "company": company,
            "market_lambda_home": float(rec["lambda_home"]),
            "market_lambda_away": float(rec["lambda_away"]),
            "market_rho": float(rec["rho"]),
            "role": "LIKELIHOOD_OR_MARKET_REFERENCE_ONLY",
        },
        "posterior_ref": {
            "engine_version": bayesian_posterior_packet.get("engine_version"),
            "status": bayesian_posterior_packet.get("status"),
            "accepted_evidence_count": bayesian_posterior_packet.get("accepted_evidence_count"),
            "prior_provenance": bayesian_posterior_packet.get("prior_provenance"),
        },
        "score_grid_ref": {
            "posterior_lambda_home_mean": summary["posterior_lambda_home_mean"],
            "posterior_lambda_away_mean": summary["posterior_lambda_away_mean"],
            "posterior_rho_mean": summary["posterior_rho_mean"],
            "model_1x2": probabilities_1x2(grid),
            "raw_top10": raw_top10,
            "five_plus_home_tail": summary["five_plus_home_tail"],
            "five_plus_away_tail": summary["five_plus_away_tail"],
            "any_team_five_plus_tail": summary["any_team_five_plus_tail"],
        },
        "top3_scores": selected,
        "top3_posterior": selected_with_probability,
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
