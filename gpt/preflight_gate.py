"""Hard pre-ticket gate for MODEL_1.

The gate exists to prevent cross-chat/process drift.  It does not predict a match and
it does not add a second opinion.  It verifies that the already-authorized MODEL_1
work was actually completed before an actionable formal ticket can be emitted.

PRECHECK_BLOCKED is not PASS.  It means the formal analysis is incomplete and must
finish the missing work before any ticket/grade is allowed.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping, Sequence


PREFLIGHT_VERSION = "MODEL_1-PREFLIGHT-1.0.0"


class PreflightGateError(ValueError):
    """Raised when MODEL_1 is not ready to emit a formal ticket."""


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
    "titan_match_identity_verified",
    "opening_only_impression_completed",
    "same_time_slice_audit_completed",
    "ah_all_main_lines_divergence_audited",
    "ah_lifecycle_audited",
    "one_x_two_ah_coherence_audited",
    "ou_independent_direction_completed",
    "score_direction_consistency_gate_passed",
    "draw_exclusion_state_loaded",
    "red_team_h2_completed",
    "red_team_h2_independent",
    "ticket_lock_ready",
)


def validate_preflight_packet(packet: Mapping[str, Any]) -> PreflightResult:
    """Validate hard readiness requirements before any formal ticket is emitted.

    Required semantics:
    - all existing MODEL_1 rules are loaded for this run;
    - Titan identity/opening/same-slice/AH lifecycle + all-line divergence are done;
    - OU has an independent OVER/UNDER direction and reference line even if no OU bet;
    - score Top3 consistency gate has passed;
    - draw-exclusion state has been loaded;
    - Red Team H2 is completed independently;
    - there is no unresolved *critical execution* conflict;
    - the ticket-lock mechanism is ready.

    Non-critical missing data are allowed when explicitly disclosed.  Missingness is
    not automatically negative evidence.
    """

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

    verdict = str(packet.get("red_team_verdict") or "").strip().upper()
    if verdict not in {"CONFIRM", "DOWNGRADE", "UPGRADE", "OVERTURN"}:
        failures.append("red_team_verdict")

    if packet.get("unresolved_critical_execution_conflict") is True:
        failures.append("unresolved_critical_execution_conflict")

    # Missing data can exist, but must be named/disclosed before ticketing.
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
    """Raise if the preflight gate is not fully satisfied."""

    result = validate_preflight_packet(packet)
    if not result.passed:
        raise PreflightGateError(
            "MODEL_1 preflight blocked formal ticket: " + ", ".join(result.failures)
        )
    return result


def packet_from_stage_evidence(
    stage_evidence: Mapping[str, Mapping[str, Any]],
    *,
    current_model_1_policy_loaded: bool,
    unresolved_critical_execution_conflict: bool = False,
) -> dict[str, Any]:
    """Build the preflight packet from formal 18-stage evidence.

    This intentionally reads already-produced stage evidence instead of asking the
    caller to manually repeat each gate result.
    """

    market = stage_evidence.get("market_snapshot", {})
    opening = stage_evidence.get("opening_first_impression", {})
    lifecycle = stage_evidence.get("opening_rationality_lifecycle", {})
    one_x_two = stage_evidence.get("one_x_two_real_vs_camouflage_open", {})
    ah = stage_evidence.get("asian_handicap_europe_asia_conversion", {})
    totals = stage_evidence.get("totals", {})
    draw = stage_evidence.get("draw_exclusion_winner_audit", {})
    score = stage_evidence.get("correct_score_poisson_bayesian", {})
    red = stage_evidence.get("red_team_h2", {})
    final = stage_evidence.get("formal_main_exactly_one", {})

    missing_core = market.get("missing_core_data")
    missing_present = bool(missing_core) and str(missing_core).strip().upper() not in {"NONE", "NO", "[]", "{}"}

    return {
        "current_model_1_policy_loaded": bool(current_model_1_policy_loaded),
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
        "red_team_h2_completed": bool(red.get("h2_alternative") and red.get("strongest_counterevidence")),
        "red_team_h2_independent": bool(red.get("independent_h2_completed", False)),
        "red_team_verdict": red.get("red_team_verdict"),
        "ticket_lock_ready": bool(final.get("ticket_locked")),
        "unresolved_critical_execution_conflict": bool(unresolved_critical_execution_conflict),
        "missing_core_data_present": missing_present,
        "missing_core_data_disclosed": (not missing_present) or bool(market.get("missing_core_data_disclosed")),
        "opening_validity_present": bool(lifecycle.get("opening_validity")),
    }
