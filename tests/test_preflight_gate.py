import pytest

from gpt.preflight_gate import PreflightGateError, require_preflight_pass, validate_preflight_packet


def _packet(draw_state="EXCLUDED"):
    packet = {
        "current_model_1_policy_loaded": True,
        "single_h1_falsification_override_loaded": True,
        "bookmaker_intent_policy_loaded": True,
        "titan_match_identity_verified": True,
        "opening_only_impression_completed": True,
        "same_time_slice_audit_completed": True,
        "bookmaker_profiles_priors_only_acknowledged": True,
        "bookmaker_role_map_completed": True,
        "bookmaker_role_map": {
            "William Hill": "LEADER",
            "Ladbrokes UK": "CONFIRMER",
            "Pinnacle": "FOLLOWER",
            "Bet365": "DIVERGENT",
            "Macau": "CONFIRMER",
            "HKJC": "STALE_OR_ASYNCHRONOUS",
        },
        "lead_follow_audit_completed": True,
        "same_time_slice_company_divergence_completed": True,
        "material_move_competing_explanations_completed": True,
        "blocking_inducement_hot_cold_audit_completed": True,
        "cross_market_correlation_guard_completed": True,
        "popular_side_default_forbidden_acknowledged": True,
        "operator_intent_conclusion": "POPULAR_SIDE_TAXED",
        "operator_intent_counterinterpretation": "TRUE_INFORMATION_REPRICING",
        "ah_all_main_lines_divergence_audited": True,
        "ah_lifecycle_audited": True,
        "one_x_two_ah_coherence_audited": True,
        "ou_independent_direction_completed": True,
        "ou_direction": "OVER",
        "ou_reference_line": 2.5,
        "score_direction_consistency_gate_passed": True,
        "draw_exclusion_state_loaded": True,
        "draw_exclusion_state": draw_state,
        "draw_excluded_binary_winner_audit_completed": draw_state == "EXCLUDED",
        "more_protected_side": "AWAY" if draw_state == "EXCLUDED" else None,
        "more_sold_side": "HOME" if draw_state == "EXCLUDED" else None,
        "winner_choice_after_intent_audit": "AWAY" if draw_state == "EXCLUDED" else None,
        "neutral_evidence_ledger_complete": True,
        "h1_contradictions_recorded": True,
        "market_rationalization_guard_complete": True,
        "falsification_audit_completed": True,
        "h1_failure_conditions_recorded": True,
        "counterevidence_tested": True,
        "alternative_match_paths_tested": True,
        "competition_rules_gate_passed": True,
        "drift_mode_acknowledged": True,
        "final_direction_survives_falsification": True,
        "falsification_verdict": "SURVIVES",
        "old_h1_discarded": False,
        "rebuilt_h1_frozen": False,
        "rebuilt_h1_rechecked": False,
        "second_formal_candidate_constructed": False,
        "ticket_lock_ready": True,
        "unresolved_critical_execution_conflict": False,
        "missing_core_data_present": False,
        "missing_core_data_disclosed": True,
    }
    return packet


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


def test_bookmaker_intent_policy_and_role_map_are_hard_gates():
    packet = _packet()
    packet["bookmaker_intent_policy_loaded"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet()
    packet["bookmaker_role_map"] = {}
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet()
    packet["bookmaker_role_map"]["Pinnacle"] = "SMART_MONEY_TRUTH"
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_lead_follow_and_blocking_inducement_audits_are_hard_gates():
    packet = _packet()
    packet["lead_follow_audit_completed"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet()
    packet["blocking_inducement_hot_cold_audit_completed"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet()
    packet["material_move_competing_explanations_completed"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_cross_market_correlation_guard_is_hard_gate():
    packet = _packet()
    packet["cross_market_correlation_guard_completed"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_draw_excluded_requires_true_binary_winner_audit():
    packet = _packet("EXCLUDED")
    packet["draw_excluded_binary_winner_audit_completed"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet("EXCLUDED")
    packet["more_protected_side"] = None
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet("EXCLUDED")
    packet["more_sold_side"] = None
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet("EXCLUDED")
    packet["winner_choice_after_intent_audit"] = None
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_not_excluded_does_not_require_binary_only_fields():
    packet = _packet("NOT_EXCLUDED")
    packet["draw_excluded_binary_winner_audit_completed"] = False
    packet["more_protected_side"] = None
    packet["more_sold_side"] = None
    packet["winner_choice_after_intent_audit"] = None
    require_preflight_pass(packet)


def test_popular_side_default_forbidden_acknowledgement_is_hard_gate():
    packet = _packet()
    packet["popular_side_default_forbidden_acknowledged"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_operator_intent_requires_conclusion_and_counterinterpretation():
    packet = _packet()
    packet["operator_intent_conclusion"] = None
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet()
    packet["operator_intent_counterinterpretation"] = None
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_single_h1_falsification_is_hard_gate():
    packet = _packet()
    packet["falsification_audit_completed"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)

    packet = _packet()
    packet["falsification_verdict"] = "CONFIRM"
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_overturn_and_rebuild_requires_rebuild_trace():
    packet = _packet()
    packet["falsification_verdict"] = "OVERTURN_AND_REBUILD"
    packet["old_h1_discarded"] = True
    packet["rebuilt_h1_frozen"] = True
    packet["rebuilt_h1_rechecked"] = True
    require_preflight_pass(packet)

    packet["rebuilt_h1_rechecked"] = False
    with pytest.raises(PreflightGateError):
        require_preflight_pass(packet)


def test_second_formal_candidate_is_forbidden():
    packet = _packet()
    packet["second_formal_candidate_constructed"] = True
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
