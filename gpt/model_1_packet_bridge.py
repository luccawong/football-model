"""MODEL_1 packet bridge.

Maps validated Quant/Feature outputs into the 18-stage formal trace without
changing the underlying mathematical engines. Formal Stage14 requires the
MODEL_1 Bayesian posterior score engine; market reconstruction alone remains
research-only.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence
from pathlib import Path

from draw_exclusion.markets import model_1_reference
from draw_exclusion.query_label import query_by_titan

from gpt.feature_engine import module_gate
from gpt.prior_engine import PriorEngineError
from gpt.prior_runtime import resolve_prior
from gpt.stage14_bayesian import build_stage14_score_packet
from gpt.stage14_auto import resolve_score_engine

PACKET_BRIDGE_VERSION = "MODEL_1-PACKET-BRIDGE-1.4.1"


class PacketBridgeError(ValueError):
    pass


def _team_goal_baseline_audit(
    *, quant_packet: Mapping[str, Any], competition: str, season: str,
    home_team: str, away_team: str, kickoff: str,
    database: str | Path | None = None,
) -> dict[str, Any]:
    """Attach audit-only team-goal context; baseline failure never blocks Stage14."""
    try:
        from gpt.team_goal_baseline import build_team_goal_baseline_packet
        kwargs: dict[str, Any] = {
            "competition": competition, "season": season,
            "home_team": home_team, "away_team": away_team,
            "kickoff": kickoff, "match_id": quant_packet.get("match_id"),
            "quant_packet": quant_packet,
        }
        if database is not None:
            kwargs["database"] = database
        audit = build_team_goal_baseline_packet(**kwargs)
        audit.setdefault("formal_model_1_weight_impact", "NONE")
        audit.setdefault("research_only", True)
        return audit
    except Exception as exc:  # research context is explicitly non-blocking
        return {
            "status": "MISSING", "reason": "BASELINE_AUDIT_ERROR", "detail": str(exc),
            "research_only": True, "formal_model_1_weight_impact": "NONE",
            "no_future_leakage": True,
        }


def _require_formal_ou_direction(
    execution_path: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Require an OU direction before any formal correct-score Top3 is emitted.

    OU_DIRECTION is mandatory even when OU_TICKET is false/no-bet. The direction
    is a score-selection constraint, not a requirement to issue an OU wager.
    """
    path = dict(execution_path or {})
    ou = path.get("ou")
    if not isinstance(ou, Mapping):
        raise PacketBridgeError(
            "OU_DIRECTION_REQUIRED: formal MODEL_1 Top3 requires execution_path.ou "
            "with side=OVER|UNDER and line; OU ticket may still be NO."
        )
    side = str(ou.get("side", "")).upper()
    if side not in {"OVER", "UNDER"} or ou.get("line") is None:
        raise PacketBridgeError(
            "OU_DIRECTION_REQUIRED: execution_path.ou must contain side=OVER|UNDER and line."
        )
    try:
        line = float(ou["line"])
    except (TypeError, ValueError) as exc:
        raise PacketBridgeError("OU_DIRECTION_REQUIRED: execution_path.ou.line must be numeric.") from exc

    ou_path = dict(ou)
    ou_path["side"] = side
    ou_path["line"] = line
    ou_path["hard_gate"] = True
    ou_path.setdefault("formal_direction", True)
    path["ou"] = ou_path
    return path


def _hard_filter_ou_top3(stage14: Mapping[str, Any]) -> dict[str, Any]:
    """Remove every final scoreline that conflicts with the mandatory OU direction.

    The raw predictive distribution/raw_top10 is never modified. This closes the
    legacy selector fallback that could refill Top3 with OU-inconsistent scores.
    """
    out = dict(stage14)
    top3 = [dict(row) for row in out.get("top3", []) if bool(row.get("ou_ok", False))]
    out["top3"] = top3
    if "execution_filtered_top3" in out:
        out["execution_filtered_top3"] = top3
    if "Top1" in out or "Top2" in out or "Top3" in out:
        out["Top1"] = top3[0] if len(top3) > 0 else None
        out["Top2"] = top3[1] if len(top3) > 1 else None
        out["Top3"] = top3[2] if len(top3) > 2 else None
    out["OU_gate_status"] = "APPLIED_HARD_DIRECTION_ONLY"
    out["ou_is_auxiliary"] = False
    out["ranking_policy"] = (
        "HARD_1X2_AH_OU_DIRECTION_GATE_THEN_POSTERIOR_PROBABILITY_AND_ROBUSTNESS"
    )
    if not top3 and out.get("status") in {"FORMAL_SCORE_TOP3", "BAYESIAN_POSTERIOR_TOP3"}:
        out["status"] = "SCORELINE_CONFLICT"
        out["reason"] = "NO_SCORELINE_SATISFIES_HARD_WINNER_AH_OU_GATES"
    return out


def build_feature_packet(
    *,
    match_id: str,
    module_records: Mapping[str, Mapping[str, Any]],
    stage_status: Mapping[str, str],
    missing_core_timelines: Sequence[str] | None = None,
    source_conflicts: Sequence[str] | None = None,
    external_draw_root: Path | None = None,
    team_goal_baseline_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create the MODEL_1 feature/QC packet without inventing missing evidence."""
    gate = module_gate(module_records)
    root = external_draw_root or Path(__file__).resolve().parents[1] / "draw_exclusion"
    teacher = model_1_reference(
        query_by_titan(root, str(match_id), market="JC"),
        query_by_titan(root, str(match_id), market="BD"),
    )
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
        "external_draw_teacher": teacher,
        "team_goal_baseline_context": dict(team_goal_baseline_context or {
            "status": "MISSING", "reason": "NOT_ATTACHED", "research_only": True,
            "formal_model_1_weight_impact": "NONE",
        }),
    }


def build_correct_score_quant_evidence(
    *,
    quant_packet: Mapping[str, Any],
    prior_packet: Mapping[str, Any] | None = None,
    prior_context: Mapping[str, Any] | None = None,
    prior_store: Mapping[str, Any] | str | Path | None = None,
    context_updates: Sequence[Mapping[str, Any]] | None = None,
    execution_path: Mapping[str, Any] | None = None,
    market_absorbed_fraction: float = 0.0,
    market_sigma_floor: float = 0.12,
    max_goals: int = 12,
    draws: int = 4000,
    company: str | None = None,
    bayesian_context_update: Mapping[str, Any] | None = None,
    final_top3: Sequence[str] | None = None,
    direction_consistency_gate: bool | None = None,
    team_goal_baseline_database: str | Path | None = None,
) -> dict[str, Any]:
    """Build formal MODEL_1 Stage14 evidence from a true Bayesian posterior.

    A validated prior is mandatory. The bridge accepts either an explicit prior
    packet or resolves one from ``prior_context`` + a calibrated Titan prior
    store. The preferred metadata key is ``competition``; legacy ``league`` is
    accepted. Only ACTIVE competition priors can enter formal Stage14.
    Pinnacle/Bet365/Macau are consumed only afterwards as the existing correlated
    market likelihood cluster.
    """
    prior_resolution = "EXPLICIT_PRIOR_PACKET"
    if prior_packet is None and prior_store is not None:
        context = prior_context
        if context is None:
            embedded = quant_packet.get("prior_context") or quant_packet.get("match_context")
            context = embedded if isinstance(embedded, Mapping) else None
        if context is None:
            raise PacketBridgeError(
                "Formal MODEL_1 Stage14 auto-prior requires prior_context with competition, season and teams."
            )
        try:
            prior_packet = resolve_prior(context, prior_store, require_active=True)
            prior_resolution = "AUTO_TITAN_HISTORICAL_PRIOR"
        except PriorEngineError as exc:
            raise PacketBridgeError(f"Formal MODEL_1 Titan prior unavailable: {exc}") from exc

    if prior_packet is None:
        raise PacketBridgeError(
            "Formal MODEL_1 Stage14 requires prior_packet or a calibrated prior_store + prior_context; "
            "market-only fallback is forbidden."
        )

    formal_execution_path = _require_formal_ou_direction(execution_path)
    stage14 = build_stage14_score_packet(
        quant_packet,
        prior_packet,
        context_updates=context_updates,
        execution_path=formal_execution_path,
        market_absorbed_fraction=market_absorbed_fraction,
        market_sigma_floor=market_sigma_floor,
        max_goals=max_goals,
        draws=draws,
    )
    stage14 = _hard_filter_ou_top3(stage14)
    if stage14.get("status") not in {"BAYESIAN_POSTERIOR_TOP3", "SCORELINE_CONFLICT"}:
        raise PacketBridgeError(
            f"Formal Stage14 unavailable: {stage14.get('reason', stage14.get('status'))}"
        )

    predictive = stage14.get("posterior_predictive", {})
    top3_rows = list(stage14.get("top3", []))
    baseline_audit = None
    context_for_audit = prior_context or quant_packet.get("prior_context") or quant_packet.get("match_context")
    if isinstance(context_for_audit, Mapping):
        baseline_audit = _team_goal_baseline_audit(
            quant_packet=quant_packet,
            competition=str(context_for_audit.get("competition") or context_for_audit.get("league") or ""),
            season=str(context_for_audit.get("season") or ""),
            home_team=str(context_for_audit.get("home_team") or ""),
            away_team=str(context_for_audit.get("away_team") or ""),
            kickoff=str(context_for_audit.get("kickoff") or context_for_audit.get("match_date") or ""),
            database=team_goal_baseline_database,
        )
    return {
        "packet_bridge_version": PACKET_BRIDGE_VERSION,
        "model_id": "MODEL_1",
        "formal_stage": "correct_score_poisson_dixon_coles_bayesian",
        "prior_resolution": prior_resolution,
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
        "OU_gate_status": stage14.get("OU_gate_status"),
        "market_reconstruction_role": "LIKELIHOOD_OR_MARKET_REFERENCE_ONLY",
        "no_market_only_fallback": True,
        "legacy_manual_top3_ignored": final_top3 is not None,
        "legacy_single_company_ignored": company is not None,
        "legacy_context_blob_preserved_only": dict(bayesian_context_update or {}),
        "legacy_direction_flag_preserved_only": direction_consistency_gate,
        "team_goal_baseline_audit": baseline_audit or {"status": "MISSING", "reason": "CONTEXT_UNAVAILABLE", "research_only": True, "formal_model_1_weight_impact": "NONE"},
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


def build_production_correct_score_evidence(
    *,
    quant_packet: Mapping[str, Any],
    competition: str,
    season: str,
    home_team: str,
    away_team: str,
    kickoff: str,
    snapshot_phase: str | None = None,
    mode: str = "AUTO",
    prior_packet: Mapping[str, Any] | None = None,
    prior_store: Mapping[str, Any] | str | Path | None = None,
    runtime_metadata: Mapping[str, Any] | None = None,
    context_updates: Sequence[Mapping[str, Any]] | None = None,
    execution_path: Mapping[str, Any] | None = None,
    market_sigma_floor: float = 0.12,
    max_goals: int = 12,
    draws: int = 4000,
    team_goal_baseline_database: str | Path | None = None,
) -> dict[str, Any]:
    """Production bridge whose default AUTO mode always chooses a formal model."""
    formal_execution_path = _require_formal_ou_direction(execution_path)
    stage14 = resolve_score_engine(
        competition, season, home_team, away_team, kickoff, quant_packet,
        snapshot_phase=snapshot_phase,
        mode=mode,
        prior_packet=prior_packet,
        prior_store=prior_store,
        runtime_metadata=runtime_metadata,
        context_updates=context_updates,
        execution_path=formal_execution_path,
        market_sigma_floor=market_sigma_floor,
        max_goals=max_goals,
        draws=draws,
    )
    stage14 = _hard_filter_ou_top3(stage14)
    if stage14.get("status") not in {
        "FORMAL_SCORE_TOP3", "BAYESIAN_POSTERIOR_TOP3", "SCORELINE_CONFLICT"
    }:
        raise PacketBridgeError(
            f"Formal Stage14 unavailable: {stage14.get('reason', stage14.get('status'))}"
        )
    baseline_audit = stage14.get("team_goal_baseline_audit") or _team_goal_baseline_audit(
        quant_packet=quant_packet, competition=competition, season=season,
        home_team=home_team, away_team=away_team, kickoff=kickoff,
        database=team_goal_baseline_database,
    )
    stage14 = dict(stage14)
    stage14["team_goal_baseline_audit"] = baseline_audit
    return {
        "packet_bridge_version": PACKET_BRIDGE_VERSION,
        "model_id": "MODEL_1",
        "formal_stage": "correct_score_auto_poisson_dixon_coles",
        "stage14": stage14,
        "score_engine_mode": stage14["score_engine_mode"],
        "prior_used": stage14["prior_used"],
        "historical_prior_activation": stage14["historical_prior_activation"],
        "top3_scores": [row["score"] for row in stage14.get("top3", [])],
        "top3_rows": list(stage14.get("top3", [])),
        "execution_path": stage14.get("execution_path", {}),
        "OU_gate_status": stage14.get("OU_gate_status"),
        "no_fake_historical_prior": stage14.get("no_fake_historical_prior", False),
        "team_goal_baseline_audit": baseline_audit,
    }
