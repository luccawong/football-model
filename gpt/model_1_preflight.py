"""Combined MODEL_1 preflight entry point.

Runs the original MODEL_1 preflight gate and the active 2026-09-14 competition
preflight extension. Both must pass before formal output is considered ready.
"""
from __future__ import annotations

from typing import Any, Mapping

from .preflight_gate import require_preflight_pass
from .preflight_competition_gate import require_competition_preflight_pass


def require_model_1_preflight_pass(
    base_packet: Mapping[str, Any],
    competition_packet: Mapping[str, Any],
) -> dict[str, Any]:
    base = require_preflight_pass(base_packet)
    competition = require_competition_preflight_pass(competition_packet)
    return {
        "status": "PREFLIGHT_PASS",
        "base_preflight": base.to_dict(),
        "competition_preflight": competition.to_dict(),
    }
