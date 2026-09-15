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
    "post_match", "post_match_result", "post_match_score", "post_match_outcome",
    "post_match_home_score", "post_match_away_score", "post_kickoff",
    "red_card_after_kickoff", "goal_event_current_match", "future_result",
    "result_of_next_match", "future_score", "next_match_score",
    "future_lineup_result", "test_target", "jcb_result",
}
_HISTORICAL_TIME_KEYS = {
    "source_match_timestamp", "historical_match_timestamp", "previous_match_timestamp",
    "source_past_match_timestamp", "historical_as_of",
}
_SCHEDULE_TIME_KEYS = {"next_fixture_date", "fixture_date", "scheduled_kickoff", "next_match_kickoff"}
_GENERIC_TIME_KEYS = {"match_date", "match_timestamp", "data_timestamp"}
_FUTURE_PATH_MARKERS = {"next_fixture", "upcoming_fixture", "next_match", "scheduled_fixture", "future_fixture"}
_PAST_PATH_MARKERS = {"previous_matches", "past_matches", "historical", "history", "recent_form"}


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
            if key_norm in _LEAKAGE_TOKENS:
                raise PrematchContextError(f"PREMATCH_LEAKAGE_FIELD:{path}.{key}")
            _scan_leakage(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for idx, child in enumerate(value):
            _scan_leakage(child, f"{path}[{idx}]")


def _scan_historical_timestamps(
    value: Any,
    kickoff: datetime,
    context_snapshot: datetime | None,
    path: str = "payload",
) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_norm = str(key).strip().lower().replace("-", "_")
            segments = set(path.lower().replace("[", ".").replace("]", "").split("."))
            if key_norm in _HISTORICAL_TIME_KEYS or (
                key_norm in _GENERIC_TIME_KEYS and not segments.intersection(_FUTURE_PATH_MARKERS)
            ):
                historical_dt = _parse_dt(child, f"{path}.{key}")
                if historical_dt >= kickoff:
                    raise PrematchContextError("HISTORICAL_FIELD_NOT_BEFORE_KICKOFF")
            elif key_norm in _SCHEDULE_TIME_KEYS or (
                key_norm in _GENERIC_TIME_KEYS and segments.intersection(_FUTURE_PATH_MARKERS)
            ):
                if context_snapshot is None:
                    raise PrematchContextError("CONTEXT_SNAPSHOT_REQUIRED_FOR_SCHEDULE")
                # The fixture date may be after kickoff; the publication/evidence
                # timestamp (validated separately) determines whether it was known
                # at the context snapshot.
                _parse_dt(child, f"{path}.{key}")
            _scan_historical_timestamps(child, kickoff, context_snapshot, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for idx, child in enumerate(value):
            _scan_historical_timestamps(child, kickoff, context_snapshot, f"{path}[{idx}]")


def validate_prematch_context_payload(
    payload: Mapping[str, Any],
    *,
    kickoff: Any | None = None,
    context_snapshot_timestamp: Any | None = None,
    market_snapshot_timestamp: Any | None = None,
) -> dict[str, Any]:
    """Validate a context payload against strict pre-kickoff information rules."""
    if not isinstance(payload, Mapping):
        raise PrematchContextError("context payload must be a mapping")
    _scan_leakage(payload)
    kick_dt = _parse_dt(kickoff, "kickoff") if kickoff is not None else None
    context_dt = (
        _parse_dt(context_snapshot_timestamp, "context_snapshot_timestamp")
        if context_snapshot_timestamp is not None else None
    )
    if kick_dt is not None:
        _scan_historical_timestamps(payload, kick_dt, context_dt)
    snap_dt = (
        _parse_dt(market_snapshot_timestamp, "market_snapshot_timestamp")
        if market_snapshot_timestamp is not None else None
    )
    evidence = payload.get("evidence_timestamp")
    evidence_dt = _parse_dt(evidence, "evidence_timestamp") if evidence is not None else None
    if evidence_dt is not None and context_dt is None:
        raise PrematchContextError("CONTEXT_SNAPSHOT_REQUIRED")
    if context_dt is not None and kick_dt is not None and context_dt > kick_dt:
        raise PrematchContextError("CONTEXT_SNAPSHOT_AFTER_KICKOFF")
    if evidence_dt is not None and context_dt is not None and evidence_dt > context_dt:
        raise PrematchContextError("EVIDENCE_AFTER_CONTEXT_SNAPSHOT")
    if evidence_dt is not None and kick_dt is not None and evidence_dt > kick_dt:
        raise PrematchContextError("EVIDENCE_AFTER_KICKOFF")
    lineup_dt = payload.get("lineup_timestamp") or payload.get("confirmed_at")
    if lineup_dt is not None:
        if context_dt is None:
            raise PrematchContextError("CONTEXT_SNAPSHOT_REQUIRED")
        if _parse_dt(lineup_dt, "lineup_timestamp") > context_dt:
            raise PrematchContextError("LINEUP_AFTER_CONTEXT_SNAPSHOT")
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
        "context_snapshot_timestamp": context_dt.isoformat() if context_dt else None,
        "market_snapshot_timestamp": snap_dt.isoformat() if snap_dt else None,
        "market_context_time_mismatch": bool(evidence_dt and snap_dt and evidence_dt > snap_dt),
        "market_absorption_status": (
            "MARKET_ALREADY_HAD_INFORMATION" if evidence_dt and snap_dt and evidence_dt <= snap_dt
            else "INFORMATION_NEWER_THAN_MARKET_SNAPSHOT" if evidence_dt and snap_dt
            else "UNKNOWN_TIMING"
        ),
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
    context_snapshot_timestamp: Any | None,
    market_snapshot_timestamp: Any | None,
    historical_overlap_fraction: float | None,
    calibration_ref: str | None,
    calibration_status: str | None,
    calibration_version: str | None,
    provenance: Mapping[str, Any] | None,
    allow_test_calibration: bool,
) -> tuple[dict[str, Any] | None, str]:
    if value is None:
        return None, "INSUFFICIENT_DATA"
    if not isinstance(value, Mapping):
        return None, "UNCERTAINTY_ONLY"
    payload = dict(value)
    payload.setdefault("source_group", source_group)
    if calibration_ref is not None:
        payload.setdefault("calibration_ref", calibration_ref)
    if calibration_status is not None:
        payload.setdefault("calibration_status", calibration_status)
    if calibration_version is not None:
        payload.setdefault("calibration_version", calibration_version)
    if provenance is not None:
        payload.setdefault("provenance", provenance)
    if context_snapshot_timestamp is not None:
        payload.setdefault("context_snapshot_timestamp", context_snapshot_timestamp)
    validate_prematch_context_payload(
        payload, kickoff=kickoff, context_snapshot_timestamp=context_snapshot_timestamp,
        market_snapshot_timestamp=market_snapshot_timestamp,
    )
    mode = str(payload.get("effect_mode", "UNCERTAINTY_ONLY")).upper()
    validated = bool(payload.get("validated", False))
    if mode == "QUANTIFIED_OBSERVATION" and not validated:
        return {
            "source_group": source_group,
            "effect_mode": mode,
            "validated": False,
            "status": "REJECTED_UNCALIBRATED",
            "reason": payload.get("reason", "UNVALIDATED_QUANTIFIED_CONTEXT"),
            "provenance": provenance,
        }, "REJECTED_UNCALIBRATED"
    if mode == "QUANTIFIED_OBSERVATION":
        approved = {"APPROVED_TRAIN_ONLY", "APPROVED_PRODUCTION"}
        calibration_status = str(payload.get("calibration_status", "")).upper()
        if calibration_status == "TEST_ONLY" and allow_test_calibration:
            pass
        elif calibration_status not in approved:
            return {
                "source_group": source_group, "effect_mode": mode, "validated": False,
                "status": "REJECTED_UNCALIBRATED",
                "reason": "CALIBRATION_GATE_REQUIRED", "provenance": provenance,
            }, "REJECTED_UNCALIBRATED"
        required = ("calibration_ref", "calibration_version", "evidence_timestamp", "provenance")
        if any(not payload.get(key) for key in required) or not payload.get("mean_log_lambda") or not payload.get("cov_log_lambda"):
            return {
                "source_group": source_group, "effect_mode": mode, "validated": False,
                "status": "REJECTED_UNCALIBRATED",
                "reason": "CALIBRATION_GATE_REQUIRED", "provenance": provenance,
            }, "REJECTED_UNCALIBRATED"
    update = {
        **payload,
        "source_group": source_group,
        "effect_mode": mode,
        "validated": validated,
        "calibration_ref": payload.get("calibration_ref", calibration_ref),
        "provenance": payload.get("provenance", provenance),
        "context_snapshot_timestamp": payload.get("context_snapshot_timestamp", context_snapshot_timestamp),
    }
    if "historical_overlap_fraction" in payload or historical_overlap_fraction is not None:
        update["historical_overlap_fraction"] = float(payload.get("historical_overlap_fraction", historical_overlap_fraction))
    if "absorbed_fraction" not in update and payload.get("evidence_timestamp") is not None and market_snapshot_timestamp is not None:
        evidence_dt = _parse_dt(payload["evidence_timestamp"], "evidence_timestamp")
        snapshot_dt = _parse_dt(market_snapshot_timestamp, "market_snapshot_timestamp")
        # Public before the market snapshot is conservatively treated as fully
        # absorbed; information first available afterwards is not absorbed.
        update["absorbed_fraction"] = 1.0 if evidence_dt <= snapshot_dt else 0.0
    if payload.get("evidence_timestamp") and market_snapshot_timestamp:
        evidence_dt = _parse_dt(payload["evidence_timestamp"], "evidence_timestamp")
        snapshot_dt = _parse_dt(market_snapshot_timestamp, "market_snapshot_timestamp")
        update["market_context_time_mismatch"] = evidence_dt > snapshot_dt
        update["market_absorption_status"] = (
            "MARKET_ALREADY_HAD_INFORMATION" if evidence_dt <= snapshot_dt
            else "INFORMATION_NEWER_THAN_MARKET_SNAPSHOT"
        )
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
    context_snapshot_timestamp: Any | None = None,
    market_snapshot_timestamp: Any | None = None,
    historical_overlap_fraction: float | None = None,
    calibration_ref: str | None = None,
    calibration_status: str | None = None,
    calibration_version: str | None = None,
    provenance: Mapping[str, Any] | None = None,
    allow_test_calibration: bool = False,
) -> dict[str, Any]:
    """Build a leakage-safe context packet for ``resolve_score_engine``.

    Real Titan result history currently supplies no calibrated context effects;
    omitted groups consequently remain non-blocking ``INSUFFICIENT_DATA``.
    """
    overlap = None if historical_overlap_fraction is None else float(historical_overlap_fraction)
    if overlap is not None and not (0.0 <= overlap <= 1.0 and isfinite(overlap)):
        raise PrematchContextError("historical_overlap_fraction must be in [0,1]")
    updates: list[dict[str, Any]] = []
    statuses: dict[str, str] = {}
    for group, value in (
        ("RECENT_FORM", recent_form), ("LINEUP", lineup),
        ("PLAYER_STATE", player_state), ("SCHEDULE", schedule),
    ):
        update, status = _prepare_update(
            group, value, kickoff=kickoff,
            context_snapshot_timestamp=context_snapshot_timestamp,
            market_snapshot_timestamp=market_snapshot_timestamp,
            historical_overlap_fraction=overlap,
            calibration_ref=calibration_ref, provenance=provenance,
            calibration_status=calibration_status, calibration_version=calibration_version,
            allow_test_calibration=allow_test_calibration,
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
        "context_snapshot_timestamp": context_snapshot_timestamp,
        "kickoff": kickoff,
        "provenance": provenance,
        "no_future_leakage": True,
    }


__all__ = [
    "CONTEXT_MODEL_VERSION", "PrematchContextError",
    "build_prematch_context_updates", "validate_prematch_context_payload",
]
