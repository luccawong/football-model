"""Deterministic decision-policy validator for the football model.

This module does not predict match outcomes. It enforces the user-approved MODEL_1
workflow, hard draw-exclusion branch, underdog-audit gate, and exactly-one-main
output policy so cross-chat execution cannot silently drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


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
    "red_team_h2",
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
    """Require the exact MODEL_1 full-analysis order.

    Extra ad-hoc stages are not accepted inside the canonical sequence. Research or
    shadow modules should run outside the frozen formal trace.
    """

    if tuple(stages) != MODEL_1_STAGE_ORDER:
        raise DecisionPolicyError(
            "MODEL_1 stage order mismatch. Expected: "
            + " -> ".join(MODEL_1_STAGE_ORDER)
        )


def resolve_draw_branch(label: object) -> DrawBranch:
    """Resolve the one-month external draw-exclusion execution branch.

    Accepted execution labels:
    - 1 / EXCLUDED / True: hard-remove draw and immediately audit HOME vs AWAY win.
    - 0 / NOT_EXCLUDED / False: retain draw and require enhanced draw audit.
    - None / UNKNOWN / absent: remain UNKNOWN; never coerce to NOT_EXCLUDED.
    """

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
    """Return whether the weak-side outright audit is mandatory.

    It is mandatory for favourites -0.75 and deeper, and is always central to a
    draw-excluded winner-only audit.
    """

    if draw_excluded:
        return True
    if favourite_handicap is None:
        return False
    return favourite_handicap <= -0.75


def validate_fundamentals_packet(packet: Mapping[str, object]) -> None:
    """Validate presence of the minimum qualitative fundamentals fields.

    Numeric opponent-quality weights are intentionally not required because MODEL_1
    forbids inventing arbitrary weights before calibration.
    """

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
    """Enforce the two user-specified market transition audits.

    1X2 must include the post-fundamentals real-open/camouflage-open audit.
    AH must include explicit European-to-Asian conversion/coherence review.
    """

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


def validate_red_team_verdict(verdict: str) -> None:
    allowed = {"CONFIRM", "DOWNGRADE", "UPGRADE", "OVERTURN"}
    if verdict not in allowed:
        raise DecisionPolicyError(
            f"Invalid Red Team verdict {verdict!r}; allowed={sorted(allowed)}"
        )


def validate_full_analysis(
    *,
    stages: Sequence[str],
    fundamentals_packet: Mapping[str, object],
    transition_flags: Mapping[str, object],
    draw_label: object,
    favourite_handicap: float | None,
    underdog_audit_completed: bool,
    red_team_verdict: str,
    ticket: TicketDecision | None,
    non_main_count: int = 0,
) -> DrawBranch:
    """Validate a completed MODEL_1 analysis trace and return the draw branch."""

    validate_stage_order(stages)
    validate_fundamentals_packet(fundamentals_packet)
    validate_market_transition_flags(transition_flags)
    branch = resolve_draw_branch(draw_label)

    if branch.enhanced_draw_audit and not transition_flags.get("enhanced_draw_audit_completed"):
        raise DecisionPolicyError("NOT_EXCLUDED requires enhanced draw audit.")
    if branch.winner_only_audit and not transition_flags.get("winner_only_audit_completed"):
        raise DecisionPolicyError("EXCLUDED requires immediate HOME-vs-AWAY winner audit.")

    if underdog_outright_audit_required(
        favourite_handicap,
        draw_excluded=branch.winner_only_audit,
    ) and not underdog_audit_completed:
        raise DecisionPolicyError("Mandatory underdog outright audit was not completed.")

    validate_red_team_verdict(red_team_verdict)
    validate_formal_ticket(ticket, non_main_count=non_main_count)
    return branch
