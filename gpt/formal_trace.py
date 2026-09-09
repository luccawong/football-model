"""MODEL_1 formal-analysis trace engine.

This module does not predict football outcomes. It records and validates the
user-approved 18-stage MODEL_1 workflow so every full analysis can be audited for
omissions, reordering, draw-branch handling, Red Team execution and exactly-one-main
output discipline.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from gpt.decision_engine import (
    MODEL_1_STAGE_ORDER,
    DecisionPolicyError,
    TicketDecision,
    resolve_draw_branch,
    underdog_outright_audit_required,
    validate_formal_ticket,
    validate_red_team_verdict,
)

TRACE_ENGINE_VERSION = "MODEL_1-TRACE-1.0.0"
ALLOWED_STAGE_STATUS = {"COMPLETE", "COMPLETE_WITH_MISSING", "CONFLICT", "BLOCKED"}


@dataclass(frozen=True)
class StageRecord:
    stage: str
    status: str
    evidence: Mapping[str, Any]
    completed_at: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class FrozenH1:
    direction: str
    market: str
    line: str
    grade: str
    frozen_at: str


@dataclass(frozen=True)
class RedTeamRecord:
    h2_alternative: str
    verdict: str
    strongest_counterevidence: Sequence[str]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def validate_stage_records(
    records: Sequence[StageRecord],
    required_fields: Mapping[str, Sequence[str]],
) -> None:
    stages = tuple(r.stage for r in records)
    if stages != MODEL_1_STAGE_ORDER:
        raise DecisionPolicyError(
            "Formal trace stage order mismatch. Expected: " + " -> ".join(MODEL_1_STAGE_ORDER)
        )

    for record in records:
        if record.status not in ALLOWED_STAGE_STATUS:
            raise DecisionPolicyError(
                f"Invalid stage status {record.status!r} for {record.stage}."
            )
        expected = required_fields.get(record.stage, ())
        missing = [field for field in expected if not _nonempty(record.evidence.get(field))]
        if missing and record.status == "COMPLETE":
            raise DecisionPolicyError(
                f"Stage {record.stage} marked COMPLETE but missing fields: {', '.join(missing)}"
            )
        if record.status == "BLOCKED":
            raise DecisionPolicyError(
                f"Formal trace cannot finish while stage {record.stage} remains BLOCKED."
            )


def validate_draw_stage(record: StageRecord) -> None:
    label = record.evidence.get("authoritative_draw_label")
    branch = resolve_draw_branch(label)

    if branch.label == "EXCLUDED":
        if not record.evidence.get("winner_only_audit_completed"):
            raise DecisionPolicyError("EXCLUDED requires winner-only HOME-vs-AWAY audit.")
        if not record.evidence.get("draw_removed_from_execution"):
            raise DecisionPolicyError("EXCLUDED requires draw removed from execution branch.")
    elif branch.label == "NOT_EXCLUDED":
        if not record.evidence.get("enhanced_draw_audit_completed"):
            raise DecisionPolicyError("NOT_EXCLUDED requires enhanced draw audit.")
        if not record.evidence.get("draw_retained_as_active_path"):
            raise DecisionPolicyError("NOT_EXCLUDED must retain draw as an active path.")
    else:
        if not record.evidence.get("unknown_disclosed"):
            raise DecisionPolicyError("UNKNOWN draw status must be explicitly disclosed.")
        if record.evidence.get("draw_removed_from_execution"):
            raise DecisionPolicyError("UNKNOWN draw status cannot hard-remove draw.")


def validate_underdog_stage(
    record: StageRecord,
    *,
    favourite_handicap: float | None,
    draw_label: object,
) -> None:
    branch = resolve_draw_branch(draw_label)
    required = underdog_outright_audit_required(
        favourite_handicap,
        draw_excluded=branch.winner_only_audit,
    )
    stated_required = bool(record.evidence.get("audit_required"))
    if required != stated_required:
        raise DecisionPolicyError(
            f"Underdog audit required={required} but trace states {stated_required}."
        )
    if required and not record.evidence.get("audit_completed"):
        raise DecisionPolicyError("Mandatory underdog outright audit not completed.")
    if required and not record.evidence.get("outright_vs_cover_separated"):
        raise DecisionPolicyError("Underdog outright audit must separate outright win from +AH cover.")


def build_formal_trace(
    *,
    match_id: str,
    model_version: str,
    policy_version: str,
    quant_engine_version: str,
    feature_engine_version: str,
    records: Sequence[StageRecord],
    required_fields: Mapping[str, Sequence[str]],
    favourite_handicap: float | None,
    h1: FrozenH1,
    red_team: RedTeamRecord,
    ticket: TicketDecision,
    non_main_count: int = 0,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Validate and return one immutable pre-match MODEL_1 trace packet."""

    validate_stage_records(records, required_fields)
    by_stage = {r.stage: r for r in records}

    draw_record = by_stage["draw_exclusion_winner_audit"]
    validate_draw_stage(draw_record)
    draw_label = draw_record.evidence.get("authoritative_draw_label")
    validate_underdog_stage(
        by_stage["underdog_outright_audit"],
        favourite_handicap=favourite_handicap,
        draw_label=draw_label,
    )

    validate_red_team_verdict(red_team.verdict)
    validate_formal_ticket(ticket, non_main_count=non_main_count)

    freeze_record = by_stage["freeze_h1"]
    if freeze_record.evidence.get("h1_direction") != h1.direction:
        raise DecisionPolicyError("Frozen H1 direction mismatch between trace and H1 object.")
    if freeze_record.evidence.get("h1_market") != h1.market:
        raise DecisionPolicyError("Frozen H1 market mismatch between trace and H1 object.")
    if freeze_record.evidence.get("h1_line") != h1.line:
        raise DecisionPolicyError("Frozen H1 line mismatch between trace and H1 object.")
    if freeze_record.evidence.get("h1_grade") != h1.grade:
        raise DecisionPolicyError("Frozen H1 grade mismatch between trace and H1 object.")

    red_record = by_stage["red_team_h2"]
    if red_record.evidence.get("red_team_verdict") != red_team.verdict:
        raise DecisionPolicyError("Red Team verdict mismatch between trace and RedTeamRecord.")

    ticket_record = by_stage["formal_main_exactly_one"]
    expected_ticket = {
        "ticket_market": ticket.market,
        "ticket_line": ticket.line,
        "ticket_direction": ticket.direction,
        "ticket_grade": ticket.grade,
        "actionable_price": ticket.actionable_price,
    }
    for key, expected in expected_ticket.items():
        if ticket_record.evidence.get(key) != expected:
            raise DecisionPolicyError(f"Ticket field mismatch for {key}.")
    if not ticket_record.evidence.get("ticket_locked"):
        raise DecisionPolicyError("Final formal main must be marked ticket_locked=true.")

    status_counts: dict[str, int] = {s: 0 for s in sorted(ALLOWED_STAGE_STATUS)}
    for record in records:
        status_counts[record.status] += 1

    return {
        "trace_engine_version": TRACE_ENGINE_VERSION,
        "model_id": "MODEL_1",
        "model_version": model_version,
        "policy_version": policy_version,
        "match_id": str(match_id),
        "created_at": created_at or _utc_now(),
        "prematch_frozen": True,
        "stage_order": list(MODEL_1_STAGE_ORDER),
        "stage_status_counts": status_counts,
        "stages": [asdict(r) for r in records],
        "draw_branch": asdict(resolve_draw_branch(draw_label)),
        "favourite_handicap": favourite_handicap,
        "h1": asdict(h1),
        "red_team": asdict(red_team),
        "formal_main": asdict(ticket),
        "non_main_count": non_main_count,
        "engines": {
            "quant": quant_engine_version,
            "feature": feature_engine_version,
        },
        "immutability": {
            "post_result_backfill_forbidden": True,
            "ticket_change_requires_explicit_correction": True,
            "future_models_must_not_rewrite_model_1_trace": True,
        },
    }
