"""Targeted MODEL_1 preflight extension for the 2026-09-14 active override.

This module preserves the canonical 18-stage order and adds hard checks that must
be satisfied before H1 freeze and final formal output.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping


VERSION = "MODEL_1-COMPETITION-PREFLIGHT-1.0.0"

_REQUIRED_TRUE_FLAGS = (
    "competition_policy_loaded",
    "probability_policy_loaded",
    "symmetric_hypothesis_comparison_completed",
    "equal_evidentiary_burden_check_passed",
    "blind_probability_shortcut_test_passed",
    "competition_winner_selected_before_h1_freeze",
)


@dataclass(frozen=True)
class CompetitionPreflightResult:
    status: str
    version: str
    passed: bool
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_competition_preflight(packet: Mapping[str, Any]) -> CompetitionPreflightResult:
    failures: list[str] = []

    for key in _REQUIRED_TRUE_FLAGS:
        if packet.get(key) is not True:
            failures.append(key)

    if packet.get("incremental_evidence_gate_applicable") is True:
        if packet.get("incremental_evidence_gate_passed") is not True:
            failures.append("incremental_evidence_gate_passed")

    if packet.get("ou_escape_hatch_check_applicable") is True:
        if packet.get("ou_escape_hatch_check_passed") is not True:
            failures.append("ou_escape_hatch_check_passed")

    if failures:
        return CompetitionPreflightResult(
            status="PRECHECK_BLOCKED_NO_TICKET",
            version=VERSION,
            passed=False,
            failures=tuple(failures),
        )

    return CompetitionPreflightResult(
        status="PREFLIGHT_EXTENSION_PASS",
        version=VERSION,
        passed=True,
        failures=(),
    )


def require_competition_preflight_pass(packet: Mapping[str, Any]) -> CompetitionPreflightResult:
    result = validate_competition_preflight(packet)
    if not result.passed:
        raise ValueError(
            "MODEL_1 competition preflight blocked formal output: "
            + ", ".join(result.failures)
        )
    return result
