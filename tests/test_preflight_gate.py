import pytest

from gpt.preflight_gate import PreflightGateError, require_preflight_pass, validate_preflight_packet


def _packet():
    return {
        "current_model_1_policy_loaded": True,
        "titan_match_identity_verified": True,
        "opening_only_impression_completed": True,
        "same_time_slice_audit_completed": True,
        "ah_all_main_lines_divergence_audited": True,
        "ah_lifecycle_audited": True,
        "one_x_two_ah_coherence_audited": True,
        "ou_independent_direction_completed": True,
        "ou_direction": "OVER",
        "ou_reference_line": 3.5,
        "score_direction_consistency_gate_passed": True,
        "draw_exclusion_state_loaded": True,
        "draw_exclusion_state": "EXCLUDED",
        "red_team_h2_completed": True,
        "red_team_h2_independent": True,
        "red_team_verdict": "CONFIRM",
        "ticket_lock_ready": True,
        "unresolved_critical_execution_conflict": False,
        "missing_core_data_present": False,
        "missing_core_data_disclosed": True,
    }


def test_preflight_passes_only_when_all_hard_gates_complete():
    result = validate_preflight_packet(_packet())
    assert result.passed is True
    assert result.status == "PREFLIGHT_PASS"


def test_missing_ou_direction_blocks_formal_ticket():
    packet = _packet()
    packet["ou_independent_direction_completed"] = False
    packet["ou_direction"] = None
    result = validate_preflight_packet(packet)
    assert result.status == "PRECHECK_BLOCKED_NO_TICKET"
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_missing_all_line_ah_divergence_audit_blocks_formal_ticket():
    packet = _packet()
    packet["ah_all_main_lines_divergence_audited"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_red_team_must_be_independent():
    packet = _packet()
    packet["red_team_h2_independent"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_missing_core_data_is_allowed_only_when_disclosed():
    packet = _packet()
    packet["missing_core_data_present"] = True
    packet["missing_core_data_disclosed"] = True
    require_preflight_pass(packet)

    packet["missing_core_data_disclosed"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)
