"""Hard pre-ticket gate for MODEL_1.

The gate exists to prevent cross-chat/process drift. It verifies that the authorized
MODEL_1 work was actually completed before any formal output can be emitted.

2026-09-16 targeted overrides:
- MODEL_1 uses one working hypothesis (H1).
- Stage 17 is a hard single-H1 falsification audit that may directly overturn and
  rebuild H1 before the only formal ticket is emitted.
- Bookmaker profiles are priors only; every match must assign actual Lead/Confirm/
  Follow/Divergence roles from the timeline.
- If draw is formally EXCLUDED, the execution branch becomes a true home-vs-away
  binary audit and the favourite/stronger/lower-odds side receives no default priority.

PRECHECK_BLOCKED is not PASS. It means the formal analysis is incomplete and must
finish the missing work before any formal output is allowed.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping


PREFLIGHT_VERSION = "MODEL_1-PREFLIGHT-1.3.0"


class PreflightGateError(ValueError):
    """Raised when MODEL_1 is not ready to emit a formal output."""


@dataclass(frozen=True)
class PreflightResult:
    status: str
    version: str
    passed: bool
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_REQUIRED_TRUE_FLAGS: tuple[str, ...] = (
    "current_model_1_policy_loaded",
    "single_h1_falsification_override_loaded",
    "bookmaker_intent_policy_loaded",
    "titan_match_identity_verified",
    "opening_only_impression_completed",
    "same_time_slice_audit_completed",
    "bookmaker_profiles_priors_only_acknowledged",
    "bookmaker_role_map_completed",
    "lead_follow_audit_completed",
    "same_time_slice_company_divergence_completed",
    "material_move_competing_explanations_completed",
    "blocking_inducement_hot_cold_audit_completed",
    "cross_market_correlation_guard_completed",
    "popular_side_default_forbidden_acknowledged",
    "ah_all_main_lines_divergence_audited",
    "ah_lifecycle_audited",
    "one_x_two_ah_coherence_audited",
    "ou_independent_direction_completed",
    "score_direction_consistency_gate_passed",
    "draw_exclusion_state_loaded",
    "neutral_evidence_ledger_complete",
    "h1_contradictions_recorded",
    "market_rationalization_guard_complete",
    "falsification_audit_completed",
    "h1_failure_conditions_recorded",
    "counterevidence_tested",
    "alternative_match_paths_tested",
    "competition_rules_gate_passed",
    "drift_mode_acknowledged",
    "final_direction_survives_falsification",
    "ticket_lock_ready",
)


_VALID_FALSIFICATION_VERDICTS = {
    "SURVIVES",
    "DOWNGRADE",
    "UPGRADE",
    "OVERTURN_AND_REBUILD",
}

_VALID_ROLE_LABELS = {
    "LEADER",
    "CONFIRMER",
    "FOLLOWER",
    "DIVERGENT",
    "STALE_OR_ASYNCHRONOUS",
    "UNKNOWN",
}


def _has_text(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _validate_bookmaker_role_map(value: Any) -> bool:
    if not isinstance(value, Mapping) or not value:
        return False
    for role in value.values():
        if str(role or "").strip().upper() not in _VALID_ROLE_LABELS:
            return False
    return True


def validate_preflight_packet(packet: Mapping[str, Any]) -> PreflightResult:
    """Validate hard readiness requirements before any formal output is emitted."""

    failures: list[str] = []
    for key in _REQUIRED_TRUE_FLAGS:
        if packet.get(key) is not True:
            failures.append(key)

    side = str(packet.get("ou_direction") or "").strip().upper()
    if side not in {"OVER", "UNDER"}:
        failures.append("ou_direction=OVER|UNDER")
    if packet.get("ou_reference_line") in (None, ""):
        failures.append("ou_reference_line")

    draw_state = str(packet.get("draw_exclusion_state") or "").strip().upper()
    if draw_state not in {"EXCLUDED", "NOT_EXCLUDED", "UNKNOWN"}:
        failures.append("draw_exclusion_state")

    role_map = packet.get("bookmaker_role_map")
    if not _validate_bookmaker_role_map(role_map):
        failures.append("bookmaker_role_map")

    if not _has_text(packet.get("operator_intent_conclusion")):
        failures.append("operator_intent_conclusion")
    if not _has_text(packet.get("operator_intent_counterinterpretation")):
        failures.append("operator_intent_counterinterpretation")

    if draw_state == "EXCLUDED":
        if packet.get("draw_excluded_binary_winner_audit_completed") is not True:
            failures.append("draw_excluded_binary_winner_audit_completed")
        if not _has_text(packet.get("more_protected_side")):
            failures.append("more_protected_side")
        if not _has_text(packet.get("more_sold_side")):
            failures.append("more_sold_side")
        if not _has_text(packet.get("winner_choice_after_intent_audit")):
            failures.append("winner_choice_after_intent_audit")

    verdict = str(packet.get("falsification_verdict") or "").strip().upper()
    if verdict not in _VALID_FALSIFICATION_VERDICTS:
        failures.append("falsification_verdict")

    if verdict == "OVERTURN_AND_REBUILD":
        if packet.get("old_h1_discarded") is not True:
            failures.append("old_h1_discarded")
        if packet.get("rebuilt_h1_frozen") is not True:
            failures.append("rebuilt_h1_frozen")
        if packet.get("rebuilt_h1_rechecked") is not True:
            failures.append("rebuilt_h1_rechecked")

    if packet.get("second_formal_candidate_constructed") is True:
        failures.append("second_formal_candidate_constructed")

    if packet.get("unresolved_critical_execution_conflict") is True:
        failures.append("unresolved_critical_execution_conflict")

    if packet.get("missing_core_data_present") is True and packet.get("missing_core_data_disclosed") is not True:
        failures.append("missing_core_data_disclosed")

    if failures:
        return PreflightResult(
            status="PRECHECK_BLOCKED_NO_TICKET",
            version=PREFLIGHT_VERSION,
            passed=False,
            failures=tuple(failures),
        )
    return PreflightResult(
        status="PREFLIGHT_PASS",
        version=PREFLIGHT_VERSION,
        passed=True,
        failures=(),
    )


def require_preflight_pass(packet: Mapping[str, Any]) -> PreflightResult:
    result = validate_preflight_packet(packet)
    if not result.passed:
        raise PreflightGateError(
            "MODEL_1 preflight blocked formal output: " + ", ".join(result.failures)
        )
    return result


def packet_from_stage_evidence(
    stage_evidence: Mapping[str, Mapping[str, Any]],
    *,
    current_model_1_policy_loaded: bool,
    unresolved_critical_execution_conflict: bool = False,
) -> dict[str, Any]:
    """Build the preflight packet from formal stage evidence.

    Stage 17 uses ``single_h1_falsification_audit``. Bookmaker-intent fields can
    be emitted by stages 4/7/8/10/11/12, but the stage-12 winner audit is the
    canonical source for draw-excluded binary fields.
    """

    market = stage_evidence.get("market_snapshot", {})
    opening = stage_evidence.get("opening_first_impression", {})
    lifecycle = stage_evidence.get("opening_rationality_lifecycle", {})
    one_x_two = stage_evidence.get("one_x_two_real_vs_camouflage_open", {})
    ah = stage_evidence.get("asian_handicap_europe_asia_conversion", {})
    totals = stage_evidence.get("totals", {})
    coherence = stage_evidence.get("cross_market_coherence", {})
    attraction = stage_evidence.get("market_attraction", {})
    uncertainty = stage_evidence.get("uncertainty_audit", {})
    draw = stage_evidence.get("draw_exclusion_winner_audit", {})
    score = stage_evidence.get("correct_score_poisson_bayesian", {})
    falsification = stage_evidence.get("single_h1_falsification_audit", {})
    final = stage_evidence.get("formal_main_exactly_one", {})

    missing_core = market.get("missing_core_data")
    missing_present = bool(missing_core) and str(missing_core).strip().upper() not in {"NONE", "NO", "[]", "{}"}

    competition_rules_relevant = bool(
        falsification.get("competition_rules_relevant", False)
        or uncertainty.get("competition_rules_relevant", False)
    )
    competition_rules_checked = bool(
        falsification.get("competition_rules_checked", False)
        or uncertainty.get("competition_rules_checked", False)
    )
    competition_rules_gate_passed = (not competition_rules_relevant) or competition_rules_checked

    verdict = str(falsification.get("falsification_verdict") or "").strip().upper()
    authoritative_draw_label = str(draw.get("authoritative_draw_label") or "").strip().upper()

    role_map = (
        one_x_two.get("bookmaker_role_map")
        or lifecycle.get("bookmaker_role_map")
        or attraction.get("bookmaker_role_map")
        or {}
    )

    operator_intent_conclusion = (
        draw.get("operator_intent_conclusion")
        or attraction.get("operator_intent_conclusion")
        or one_x_two.get("operator_intent_conclusion")
    )
    operator_intent_counterinterpretation = (
        draw.get("operator_intent_counterinterpretation")
        or attraction.get("operator_intent_counterinterpretation")
        or one_x_two.get("operator_intent_counterinterpretation")
    )

    return {
        "current_model_1_policy_loaded": bool(current_model_1_policy_loaded),
        "single_h1_falsification_override_loaded": bool(
            falsification.get("single_h1_override_loaded")
            or falsification.get("targeted_override_loaded")
        ),
        "bookmaker_intent_policy_loaded": bool(
            lifecycle.get("bookmaker_intent_policy_loaded")
            or one_x_two.get("bookmaker_intent_policy_loaded")
            or attraction.get("bookmaker_intent_policy_loaded")
            or draw.get("bookmaker_intent_policy_loaded")
        ),
        "titan_match_identity_verified": bool(market.get("match_identity_qc")),
        "opening_only_impression_completed": bool(opening.get("opening_only_view") and opening.get("opening_structure_conclusion")),
        "same_time_slice_audit_completed": bool(one_x_two.get("same_time_slice_comparison")),
        "bookmaker_profiles_priors_only_acknowledged": bool(
            lifecycle.get("bookmaker_profiles_priors_only_acknowledged")
            or one_x_two.get("bookmaker_profiles_priors_only_acknowledged")
        ),
        "bookmaker_role_map_completed": _validate_bookmaker_role_map(role_map),
        "bookmaker_role_map": role_map,
        "lead_follow_audit_completed": bool(
            lifecycle.get("lead_follow_audit_completed")
            or one_x_two.get("lead_follow_audit_completed")
        ),
        "same_time_slice_company_divergence_completed": bool(
            one_x_two.get("same_time_slice_company_divergence_completed")
            or ah.get("same_time_slice_company_divergence_completed")
        ),
        "material_move_competing_explanations_completed": bool(
            lifecycle.get("material_move_competing_explanations_completed")
            or uncertainty.get("material_move_competing_explanations_completed")
        ),
        "blocking_inducement_hot_cold_audit_completed": bool(
            attraction.get("blocking_inducement_hot_cold_audit_completed")
            or draw.get("blocking_inducement_hot_cold_audit_completed")
        ),
        "cross_market_correlation_guard_completed": bool(
            coherence.get("cross_market_correlation_guard_completed")
            or uncertainty.get("cross_market_correlation_guard_completed")
        ),
        "popular_side_default_forbidden_acknowledged": bool(
            attraction.get("popular_side_default_forbidden_acknowledged")
            or draw.get("popular_side_default_forbidden_acknowledged")
        ),
        "operator_intent_conclusion": operator_intent_conclusion,
        "operator_intent_counterinterpretation": operator_intent_counterinterpretation,
        "ah_all_main_lines_divergence_audited": bool(ah.get("ah_all_main_lines_divergence_audited")),
        "ah_lifecycle_audited": bool(ah.get("ah_lifecycle") and ah.get("water_lifecycle")),
        "one_x_two_ah_coherence_audited": bool(ah.get("europe_asia_conversion_audited")),
        "ou_independent_direction_completed": bool(totals.get("ou_independent_conclusion")),
        "ou_direction": totals.get("ou_direction"),
        "ou_reference_line": totals.get("ou_reference_line"),
        "score_direction_consistency_gate_passed": bool(score.get("direction_consistency_gate")),
        "draw_exclusion_state_loaded": "authoritative_draw_label" in draw,
        "draw_exclusion_state": authoritative_draw_label,
        "draw_excluded_binary_winner_audit_completed": bool(
            draw.get("draw_excluded_binary_winner_audit_completed")
        ),
        "more_protected_side": draw.get("more_protected_side"),
        "more_sold_side": draw.get("more_sold_side"),
        "winner_choice_after_intent_audit": draw.get("winner_choice_after_intent_audit"),
        "neutral_evidence_ledger_complete": bool(uncertainty.get("neutral_evidence_ledger_complete")),
        "h1_contradictions_recorded": bool(uncertainty.get("h1_contradictions_recorded")),
        "market_rationalization_guard_complete": bool(
            uncertainty.get("market_rationalization_guard_complete")
            or falsification.get("market_rationalization_guard_complete")
        ),
        "falsification_audit_completed": bool(falsification.get("falsification_audit_completed")),
        "h1_failure_conditions_recorded": bool(falsification.get("h1_failure_conditions_recorded")),
        "counterevidence_tested": bool(falsification.get("counterevidence_tested")),
        "alternative_match_paths_tested": bool(falsification.get("alternative_match_paths_tested")),
        "competition_rules_gate_passed": bool(competition_rules_gate_passed),
        "drift_mode_acknowledged": bool(falsification.get("drift_mode_acknowledged", False)),
        "final_direction_survives_falsification": bool(falsification.get("final_direction_survives_falsification", False)),
        "falsification_verdict": verdict,
        "old_h1_discarded": bool(falsification.get("old_h1_discarded", False)),
        "rebuilt_h1_frozen": bool(falsification.get("rebuilt_h1_frozen", False)),
        "rebuilt_h1_rechecked": bool(falsification.get("rebuilt_h1_rechecked", False)),
        "second_formal_candidate_constructed": bool(falsification.get("second_formal_candidate_constructed", False)),
        "ticket_lock_ready": bool(final.get("ticket_locked")),
        "unresolved_critical_execution_conflict": bool(unresolved_critical_execution_conflict),
        "missing_core_data_present": missing_present,
        "missing_core_data_disclosed": (not missing_present) or bool(market.get("missing_core_data_disclosed")),
        "opening_validity_present": bool(lifecycle.get("opening_validity")),
    }
