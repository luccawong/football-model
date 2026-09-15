"""Deterministic decision-policy validator for the football model.

This module does not predict match outcomes. It enforces the user-approved MODEL_1
workflow, hard draw-exclusion branch, underdog-audit gate, single-H1 falsification,
and exactly-one-main output policy so cross-chat execution cannot silently drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


MODEL_ID = "MODEL_1"

MODEL_1_STAGE_ORDER: tuple[str, ...] = (
    "fundamentals",
    "market_snapshot",
    "opening_first_impression",
    "opening_rationality_lifecycle",
    "off_field_weather",
    "lineup_tactics",
    "one_x_two_real_vs_camouflage_open",
    "asian_handicap_europe_asia_conversion",
    "totals",
    "cross_market_coherence",
    "market_attraction",
    "draw_exclusion_winner_audit",
    "underdog_outright_audit",
    "correct_score_poisson_bayesian",
    "uncertainty_audit",
    "freeze_h1",
    "single_h1_falsification_audit",
    "formal_main_exactly_one",
)


class DecisionPolicyError(ValueError):
    """Raised when a full-analysis trace violates the active MODEL_1 contract."""


@dataclass(frozen=True)
class DrawBranch:
    label: str
    draw_in_execution: bool
    winner_only_audit: bool
    enhanced_draw_audit: bool


@dataclass(frozen=True)
class TicketDecision:
    market: str
    line: str
    grade: str
    actionable_price: str
    direction: str


def validate_stage_order(stages: Sequence[str]) -> None:
    """Require the exact effective MODEL_1 full-analysis order."""
    if tuple(stages) != MODEL_1_STAGE_ORDER:
        raise DecisionPolicyError(
            "MODEL_1 stage order mismatch. Expected: "
            + " -> ".join(MODEL_1_STAGE_ORDER)
        )


def resolve_draw_branch(label: object) -> DrawBranch:
    """Resolve the one-month external draw-exclusion execution branch."""
    if label in (1, True, "1", "EXCLUDED"):
        return DrawBranch(
            label="EXCLUDED",
            draw_in_execution=False,
            winner_only_audit=True,
            enhanced_draw_audit=False,
        )
    if label in (0, False, "0", "NOT_EXCLUDED"):
        return DrawBranch(
            label="NOT_EXCLUDED",
            draw_in_execution=True,
            winner_only_audit=False,
            enhanced_draw_audit=True,
        )
    return DrawBranch(
        label="UNKNOWN",
        draw_in_execution=True,
        winner_only_audit=False,
        enhanced_draw_audit=False,
    )


def underdog_outright_audit_required(
    favourite_handicap: float | None,
    *,
    draw_excluded: bool = False,
) -> bool:
    """Return whether the weak-side outright audit is mandatory."""
    if draw_excluded:
        return True
    if favourite_handicap is None:
        return False
    return favourite_handicap <= -0.75


def validate_fundamentals_packet(packet: Mapping[str, object]) -> None:
    required = {
        "recent_match_by_match",
        "opponent_quality_review",
        "wins_how_and_against_whom",
        "losses_how_and_against_whom",
        "future_schedule",
    }
    missing = sorted(k for k in required if not packet.get(k))
    if missing:
        raise DecisionPolicyError(
            "Fundamentals packet missing required fields: " + ", ".join(missing)
        )


def validate_market_transition_flags(flags: Mapping[str, object]) -> None:
    if not flags.get("real_vs_camouflage_open_audited"):
        raise DecisionPolicyError("Missing 实开/韬开 audit after fundamentals in 1X2 stage.")
    if not flags.get("europe_asia_conversion_audited"):
        raise DecisionPolicyError("Missing 1X2 -> AH 欧亚转换 consistency audit.")


def validate_formal_ticket(ticket: TicketDecision | None, non_main_count: int = 0) -> None:
    """MODEL_1 requires exactly one formal main, no non-main and no final PASS."""
    if ticket is None:
        raise DecisionPolicyError("MODEL_1 requires exactly one formal main ticket.")
    if non_main_count != 0:
        raise DecisionPolicyError("MODEL_1 abolishes non-main tickets.")
    if ticket.direction.strip().upper() == "PASS":
        raise DecisionPolicyError("MODEL_1 does not allow final PASS.")
    if not all(
        value.strip()
        for value in (
            ticket.market,
            ticket.line,
            ticket.grade,
            ticket.actionable_price,
            ticket.direction,
        )
    ):
        raise DecisionPolicyError(
            "Formal ticket must include market, line, grade, actionable price and direction."
        )


def validate_falsification_verdict(verdict: str) -> None:
    allowed = {"SURVIVES", "DOWNGRADE", "UPGRADE", "OVERTURN_AND_REBUILD"}
    if verdict not in allowed:
        raise DecisionPolicyError(
            f"Invalid falsification verdict {verdict!r}; allowed={sorted(allowed)}"
        )


def validate_red_team_verdict(verdict: str) -> None:
    """Deprecated compatibility validator for archived pre-2026-09-16 traces only."""
    allowed = {"CONFIRM", "DOWNGRADE", "UPGRADE", "OVERTURN"}
    if verdict not in allowed:
        raise DecisionPolicyError(
            f"Invalid legacy Red Team verdict {verdict!r}; allowed={sorted(allowed)}"
        )


def validate_full_analysis(
    *,
    stages: Sequence[str],
    fundamentals_packet: Mapping[str, object],
    transition_flags: Mapping[str, object],
    draw_label: object,
    favourite_handicap: float | None,
    underdog_audit_completed: bool,
    falsification_verdict: str,
    ticket: TicketDecision | None,
    non_main_count: int = 0,
) -> DrawBranch:
    """Validate a completed effective MODEL_1 analysis trace and return the draw branch."""
    validate_stage_order(stages)
    validate_fundamentals_packet(fundamentals_packet)
    validate_market_transition_flags(transition_flags)
    branch = resolve_draw_branch(draw_label)

    if branch.enhanced_draw_audit and not transition_flags.get("enhanced_draw_audit_completed"):
        raise DecisionPolicyError("NOT_EXCLUDED requires enhanced draw audit.")
    if branch.winner_only_audit and not transition_flags.get("winner_only_audit_completed"):
        raise DecisionPolicyError("EXCLUDED requires immediate HOME-vs-AWAY winner audit.")
    if branch.winner_only_audit and not transition_flags.get("draw_excluded_binary_winner_audit_completed"):
        raise DecisionPolicyError("EXCLUDED requires bookmaker-intent binary winner audit.")
    if branch.winner_only_audit and not transition_flags.get("popular_side_default_forbidden_acknowledged"):
        raise DecisionPolicyError("EXCLUDED binary audit cannot default to the favourite/popular side.")

    if underdog_outright_audit_required(
        favourite_handicap,
        draw_excluded=branch.winner_only_audit,
    ) and not underdog_audit_completed:
        raise DecisionPolicyError("Mandatory underdog outright audit was not completed.")

    validate_falsification_verdict(falsification_verdict)
    validate_formal_ticket(ticket, non_main_count=non_main_count)
    return branch
