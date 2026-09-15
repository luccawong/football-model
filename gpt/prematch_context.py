"""MODEL_1 pre-match context contract and leakage-safe validators.

The Titan result-only dataset does not contain production-calibrated lineup,
player-state, schedule or recent-form effects.  This module therefore exposes a
strict interface: unvalidated/narrative inputs are audited but never converted
into a lambda shift.  Callers may provide a quantitatively calibrated
observation, or an uncertainty-only covariance inflation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any, Mapping

CONTEXT_MODEL_VERSION = "MODEL_1-PREMATCH-CONTEXT-1.0.0"
ALLOWED_SOURCE_GROUPS = {"RECENT_FORM", "LINEUP", "PLAYER_STATE", "SCHEDULE"}
_LEAKAGE_TOKENS = {
    "actual_score", "actual_result", "final_score", "home_score", "away_score",
    "post_match", "post_match_result", "post_kickoff", "red_card_after_kickoff",
    "goal_event", "future_result", "result_of_next_match", "test_target",
    "jcb_result", "result", "score", "goals", "match_result",
}


class PrematchContextError(ValueError):
    pass


def _parse_dt(value: Any, field: str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        text = value.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise PrematchContextError(f"{field} must be ISO datetime") from exc
    else:
        raise PrematchContextError(f"{field} must be datetime or ISO datetime")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _scan_leakage(value: Any, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_norm = str(key).strip().lower().replace("-", "_")
            if key_norm in _LEAKAGE_TOKENS or any(token in key_norm for token in _LEAKAGE_TOKENS):
                raise PrematchContextError(f"PREMATCH_LEAKAGE_FIELD:{path}.{key}")
            _scan_leakage(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for idx, child in enumerate(value):
            _scan_leakage(child, f"{path}[{idx}]")


def validate_prematch_context_payload(
    payload: Mapping[str, Any],
    *,
    kickoff: Any | None = None,
    market_snapshot_timestamp: Any | None = None,
) -> dict[str, Any]:
    """Validate a context payload against strict pre-kickoff information rules."""
    if not isinstance(payload, Mapping):
        raise PrematchContextError("context payload must be a mapping")
    _scan_leakage(payload)
    kick_dt = _parse_dt(kickoff, "kickoff") if kickoff is not None else None
    snap_dt = (
        _parse_dt(market_snapshot_timestamp, "market_snapshot_timestamp")
        if market_snapshot_timestamp is not None else None
    )
    evidence = payload.get("evidence_timestamp")
    evidence_dt = _parse_dt(evidence, "evidence_timestamp") if evidence is not None else None
    if evidence_dt is not None and kick_dt is not None and evidence_dt > kick_dt:
        raise PrematchContextError("EVIDENCE_AFTER_KICKOFF")
    if evidence_dt is not None and snap_dt is not None and evidence_dt > snap_dt:
        # Information released after the market snapshot cannot be absorbed by
        # the market likelihood; it remains a pre-kickoff context observation.
        pass
    lineup_dt = payload.get("lineup_timestamp") or payload.get("confirmed_at")
    if lineup_dt is not None and snap_dt is not None and _parse_dt(lineup_dt, "lineup_timestamp") > snap_dt:
        raise PrematchContextError("LINEUP_AFTER_MARKET_SNAPSHOT")
    group = str(payload.get("source_group", ""))
    if group and group not in ALLOWED_SOURCE_GROUPS:
        raise PrematchContextError(f"UNSUPPORTED_CONTEXT_SOURCE_GROUP:{group}")
    mode = str(payload.get("effect_mode", "UNCERTAINTY_ONLY")).upper()
    if mode not in {"QUANTIFIED_OBSERVATION", "UNCERTAINTY_ONLY"}:
        raise PrematchContextError(f"UNSUPPORTED_EFFECT_MODE:{mode}")
    return {
        "status": "VALIDATED_PREMATCH_PAYLOAD",
        "source_group": group or None,
        "effect_mode": mode,
        "evidence_timestamp": evidence_dt.isoformat() if evidence_dt else None,
        "market_snapshot_timestamp": snap_dt.isoformat() if snap_dt else None,
        "kickoff": kick_dt.isoformat() if kick_dt else None,
    }


def _default_status(value: Any) -> str:
    if value is None:
        return "INSUFFICIENT_DATA"
    if isinstance(value, Mapping) and value.get("validated") is True:
        return "VALIDATED"
    return "UNCERTAINTY_ONLY"


def _prepare_update(
    source_group: str,
    value: Any,
    *,
    kickoff: Any | None,
    market_snapshot_timestamp: Any | None,
    historical_overlap_fraction: float,
    calibration_ref: str | None,
    provenance: Mapping[str, Any] | None,
) -> tuple[dict[str, Any] | None, str]:
    if value is None:
        return None, "INSUFFICIENT_DATA"
    if not isinstance(value, Mapping):
        return None, "UNCERTAINTY_ONLY"
    payload = dict(value)
    payload.setdefault("source_group", source_group)
    validate_prematch_context_payload(
        payload, kickoff=kickoff, market_snapshot_timestamp=market_snapshot_timestamp
    )
    mode = str(payload.get("effect_mode", "UNCERTAINTY_ONLY")).upper()
    validated = bool(payload.get("validated", False))
    if mode == "QUANTIFIED_OBSERVATION" and not validated:
        return {
            "source_group": source_group,
            "effect_mode": mode,
            "validated": False,
            "reason": payload.get("reason", "UNVALIDATED_QUANTIFIED_CONTEXT"),
            "provenance": provenance,
        }, "REJECTED_UNVALIDATED"
    update = {
        **payload,
        "source_group": source_group,
        "effect_mode": mode,
        "validated": validated,
        "historical_overlap_fraction": float(payload.get("historical_overlap_fraction", historical_overlap_fraction)),
        "calibration_ref": payload.get("calibration_ref", calibration_ref),
        "provenance": payload.get("provenance", provenance),
    }
    if "absorbed_fraction" not in update and payload.get("evidence_timestamp") is not None and market_snapshot_timestamp is not None:
        evidence_dt = _parse_dt(payload["evidence_timestamp"], "evidence_timestamp")
        snapshot_dt = _parse_dt(market_snapshot_timestamp, "market_snapshot_timestamp")
        # Public before the market snapshot is conservatively treated as fully
        # absorbed; information first available afterwards is not absorbed.
        update["absorbed_fraction"] = 1.0 if evidence_dt <= snapshot_dt else 0.0
    if "market_snapshot_timestamp" not in update and market_snapshot_timestamp is not None:
        update["market_snapshot_timestamp"] = market_snapshot_timestamp
    if "kickoff" not in update and kickoff is not None:
        update["kickoff"] = kickoff
    return update, "VALIDATED" if validated else "UNCERTAINTY_ONLY"


def build_prematch_context_updates(
    *,
    recent_form: Any = None,
    lineup: Any = None,
    player_state: Any = None,
    schedule: Any = None,
    kickoff: Any | None = None,
    market_snapshot_timestamp: Any | None = None,
    historical_overlap_fraction: float = 0.0,
    calibration_ref: str | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a leakage-safe context packet for ``resolve_score_engine``.

    Real Titan result history currently supplies no calibrated context effects;
    omitted groups consequently remain non-blocking ``INSUFFICIENT_DATA``.
    """
    overlap = float(historical_overlap_fraction)
    if not (0.0 <= overlap <= 1.0 and isfinite(overlap)):
        raise PrematchContextError("historical_overlap_fraction must be in [0,1]")
    updates: list[dict[str, Any]] = []
    statuses: dict[str, str] = {}
    for group, value in (
        ("RECENT_FORM", recent_form), ("LINEUP", lineup),
        ("PLAYER_STATE", player_state), ("SCHEDULE", schedule),
    ):
        update, status = _prepare_update(
            group, value, kickoff=kickoff,
            market_snapshot_timestamp=market_snapshot_timestamp,
            historical_overlap_fraction=overlap,
            calibration_ref=calibration_ref, provenance=provenance,
        )
        statuses[group] = status
        if update is not None:
            updates.append(update)
    return {
        "context_model_version": CONTEXT_MODEL_VERSION,
        "updates": updates,
        "source_status": statuses,
        "real_titan_calibration": "NONE_RESULT_ONLY_DATASET",
        "historical_overlap_fraction": overlap,
        "market_snapshot_timestamp": market_snapshot_timestamp,
        "kickoff": kickoff,
        "provenance": provenance,
        "no_future_leakage": True,
    }


__all__ = [
    "CONTEXT_MODEL_VERSION", "PrematchContextError",
    "build_prematch_context_updates", "validate_prematch_context_payload",
]
