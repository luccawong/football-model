"""Hard pre-ticket gate for MODEL_1.

The gate exists to prevent cross-chat/process drift. It verifies that the authorized
MODEL_1 work was actually completed before any formal output can be emitted.

2026-09-16 targeted override:
- MODEL_1 uses one working hypothesis (H1).
- The former mandatory independent H2/counter-ticket construction is removed.
- Stage 17 is a hard single-H1 falsification audit that may directly overturn and
  rebuild H1 before the only formal ticket is emitted.

PRECHECK_BLOCKED is not PASS. It means the formal analysis is incomplete and must
finish the missing work before any formal output is allowed.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping


PREFLIGHT_VERSION = "MODEL_1-PREFLIGHT-1.2.0"


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
    "titan_match_identity_verified",
    "opening_only_impression_completed",
    "same_time_slice_audit_completed",
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

    New callers should provide ``single_h1_falsification_audit``. During the
    transition, a legacy ``red_team_h2`` mapping can still be read as the source
    container, but no H2 candidate, blindness protocol, or H1-vs-H2 adjudication
    is required or accepted as a formal prerequisite.
    """

    market = stage_evidence.get("market_snapshot", {})
    opening = stage_evidence.get("opening_first_impression", {})
    lifecycle = stage_evidence.get("opening_rationality_lifecycle", {})
    one_x_two = stage_evidence.get("one_x_two_real_vs_camouflage_open", {})
    ah = stage_evidence.get("asian_handicap_europe_asia_conversion", {})
    totals = stage_evidence.get("totals", {})
    uncertainty = stage_evidence.get("uncertainty_audit", {})
    draw = stage_evidence.get("draw_exclusion_winner_audit", {})
    score = stage_evidence.get("correct_score_poisson_bayesian", {})
    falsification = stage_evidence.get(
        "single_h1_falsification_audit",
        stage_evidence.get("red_team_h2", {}),
    )
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

    return {
        "current_model_1_policy_loaded": bool(current_model_1_policy_loaded),
        "single_h1_falsification_override_loaded": bool(
            falsification.get("single_h1_override_loaded")
            or falsification.get("targeted_override_loaded")
        ),
        "titan_match_identity_verified": bool(market.get("match_identity_qc")),
        "opening_only_impression_completed": bool(opening.get("opening_only_view") and opening.get("opening_structure_conclusion")),
        "same_time_slice_audit_completed": bool(one_x_two.get("same_time_slice_comparison")),
        "ah_all_main_lines_divergence_audited": bool(ah.get("ah_all_main_lines_divergence_audited")),
        "ah_lifecycle_audited": bool(ah.get("ah_lifecycle") and ah.get("water_lifecycle")),
        "one_x_two_ah_coherence_audited": bool(ah.get("europe_asia_conversion_audited")),
        "ou_independent_direction_completed": bool(totals.get("ou_independent_conclusion")),
        "ou_direction": totals.get("ou_direction"),
        "ou_reference_line": totals.get("ou_reference_line"),
        "score_direction_consistency_gate_passed": bool(score.get("direction_consistency_gate")),
        "draw_exclusion_state_loaded": "authoritative_draw_label" in draw,
        "draw_exclusion_state": draw.get("authoritative_draw_label"),
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
