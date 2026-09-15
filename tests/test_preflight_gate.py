import pytest

from gpt.preflight_gate import PreflightGateError, require_preflight_pass, validate_preflight_packet


def _packet():
    return {
        "current_model_1_policy_loaded": True,
        "targeted_red_team_override_loaded": True,
        "titan_match_identity_verified": True,
        "opening_only_impression_completed": True,
        "same_time_slice_audit_completed": True,
        "ah_all_main_lines_divergence_audited": True,
        "ah_lifecycle_audited": True,
        "one_x_two_ah_coherence_audited": True,
        "ou_independent_direction_completed": True,
        "ou_direction": "OVER",
        "ou_reference_line": 2.5,
        "score_direction_consistency_gate_passed": True,
        "draw_exclusion_state_loaded": True,
        "draw_exclusion_state": "EXCLUDED",
        "neutral_evidence_ledger_complete": True,
        "h1_contradictions_recorded": True,
        "market_rationalization_guard_complete": True,
        "red_team_h2_completed": True,
        "red_team_h2_independent": True,
        "red_team_h2_blind_to_h1": True,
        "red_team_h1_visible_during_h2": False,
        "red_team_h2_fresh_reconstruction": True,
        "red_team_h2_independent_candidate_frozen": True,
        "red_team_independent_candidate": {
            "market": "TEST_MARKET",
            "line": 0.0,
            "side": "A",
            "confidence": "B",
        },
        "h1_revealed_after_h2_freeze": True,
        "h1_h2_equal_status_adjudication_complete": True,
        "drift_mode_acknowledged": True,
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
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_missing_all_line_ah_divergence_audit_blocks_formal_ticket():
    packet = _packet()
    packet["ah_all_main_lines_divergence_audited"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_red_team_must_be_blind_and_independent():
    packet = _packet()
    packet["red_team_h2_blind_to_h1"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet()
    packet["red_team_h1_visible_during_h2"] = True
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_red_team_requires_fresh_independent_candidate():
    packet = _packet()
    packet["red_team_h2_fresh_reconstruction"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet()
    packet["red_team_independent_candidate"] = None
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_h1_h2_equal_status_adjudication_is_hard_gate():
    packet = _packet()
    packet["h1_revealed_after_h2_freeze"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet()
    packet["h1_h2_equal_status_adjudication_complete"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_neutral_evidence_ledger_and_rationalization_guard_are_hard_gates():
    packet = _packet()
    packet["neutral_evidence_ledger_complete"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet()
    packet["market_rationalization_guard_complete"] = False
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
