import pytest

from gpt.decision_engine import (
    MODEL_1_STAGE_ORDER,
    DecisionPolicyError,
    TicketDecision,
    resolve_draw_branch,
    underdog_outright_audit_required,
    validate_formal_ticket,
    validate_stage_order,
)


def test_stage_order_exact():
    validate_stage_order(MODEL_1_STAGE_ORDER)
    with pytest.raises(DecisionPolicyError):
        validate_stage_order(MODEL_1_STAGE_ORDER[1:])


def test_draw_excluded_is_hard_winner_only_branch():
    branch = resolve_draw_branch(1)
    assert branch.label == "EXCLUDED"
    assert branch.draw_in_execution is False
    assert branch.winner_only_audit is True
    assert branch.enhanced_draw_audit is False


def test_not_excluded_keeps_draw_and_requires_enhanced_audit():
    branch = resolve_draw_branch(0)
    assert branch.label == "NOT_EXCLUDED"
    assert branch.draw_in_execution is True
    assert branch.enhanced_draw_audit is True


def test_unknown_never_coerces_to_not_excluded():
    branch = resolve_draw_branch(None)
    assert branch.label == "UNKNOWN"
    assert branch.enhanced_draw_audit is False


def test_underdog_audit_trigger():
    assert underdog_outright_audit_required(-0.75) is True
    assert underdog_outright_audit_required(-0.5) is False
    assert underdog_outright_audit_required(None, draw_excluded=True) is True


def test_exactly_one_formal_main_no_pass():
    ticket = TicketDecision(
        market="AH",
        line="-0.75",
        grade="B",
        actionable_price=">=1.80",
        direction="HOME -0.75",
    )
    validate_formal_ticket(ticket, non_main_count=0)

    with pytest.raises(DecisionPolicyError):
        validate_formal_ticket(None)

    with pytest.raises(DecisionPolicyError):
        validate_formal_ticket(ticket, non_main_count=1)

    with pytest.raises(DecisionPolicyError):
        validate_formal_ticket(
            TicketDecision(
                market="AH",
                line="-0.75",
                grade="C",
                actionable_price=">=1.80",
                direction="PASS",
            )
        )
