from datetime import datetime, timezone, timedelta

import numpy as np
import pytest

from gpt.prematch_context import (
    CONTEXT_MODEL_VERSION,
    PrematchContextError,
    build_prematch_context_updates,
    validate_prematch_context_payload,
)
from gpt.stage14_auto import resolve_score_engine
from gpt.stage14_bayesian import (
    BayesianScoreError,
    apply_validated_context_updates,
    build_formal_market_score_packet,
)


def quant_packet():
    rows = {}
    for company, lh, la in (
        ("Pinnacle", 1.75, 1.10), ("Bet365", 1.80, 1.08), ("Macau", 1.72, 1.13),
        ("William Hill", 2.40, 0.70), ("Ladbrokes", 2.30, 0.72), ("Interwetten", 2.20, 0.75),
    ):
        rows[company] = {"lambda_home": lh, "lambda_away": la, "rho": 0.02, "max_abs_residual": 0.001}
    return {"match_id": "ctx-1", "reconstruction": rows}


def prior_packet():
    return {
        "status": "VALID", "activation": "ACTIVE",
        "mean_log_lambda": [0.2, -0.05], "cov_log_lambda": [[0.25, 0.02], [0.02, 0.22]],
        "source_groups": ["TEAM_DATA"],
    }


def test_quantified_context_changes_market_only_lambda_and_extra_books_do_not():
    base = build_formal_market_score_packet(quant_packet(), draws=500)
    context = build_prematch_context_updates(
        recent_form={
            "validated": True, "effect_mode": "QUANTIFIED_OBSERVATION",
            "mean_log_lambda": [0.9, -0.1], "cov_log_lambda": [[0.08, 0], [0, 0.08]],
            "absorbed_fraction": 0.0, "evidence_timestamp": "2026-01-01T10:00:00Z",
            "calibration_ref": "synthetic-test", "calibration_status": "TEST_ONLY",
            "calibration_version": "test-v1", "provenance": {"source": "synthetic"},
        },
        kickoff="2026-01-01T15:00:00Z", context_snapshot_timestamp="2026-01-01T11:00:00Z",
        market_snapshot_timestamp="2026-01-01T12:00:00Z", allow_test_calibration=True,
    )
    updated = build_formal_market_score_packet(quant_packet(), context_updates=context, draws=500, allow_test_calibration=True)
    assert updated["context_model_version"] == CONTEXT_MODEL_VERSION
    assert updated["lambda_home"] != pytest.approx(base["lambda_home"])
    trimmed = quant_packet(); trimmed["reconstruction"] = {k: v for k, v in trimmed["reconstruction"].items() if k in {"Pinnacle", "Bet365", "Macau"}}
    assert build_formal_market_score_packet(trimmed, draws=500)["base_market_mean_log_lambda"] == pytest.approx(base["base_market_mean_log_lambda"])


def test_quantified_context_is_available_on_historical_bayesian_path():
    context = build_prematch_context_updates(
        lineup={
            "validated": True, "effect_mode": "QUANTIFIED_OBSERVATION",
            "mean_log_lambda": [0.6, -0.2], "cov_log_lambda": [[0.1, 0], [0, 0.1]],
            "absorbed_fraction": 0.0, "historical_overlap_fraction": 0.0, "calibration_ref": "synthetic-historical",
            "evidence_timestamp": "2026-01-01T11:00:00Z",
            "calibration_status": "TEST_ONLY", "calibration_version": "test-v1",
            "provenance": {"source": "synthetic", "not_in_historical_prior": True},
        }
        , context_snapshot_timestamp="2026-01-01T12:00:00Z", kickoff="2026-01-01T15:00:00Z",
        allow_test_calibration=True,
    )
    out = resolve_score_engine(
        "UCL", "2025-26", "A", "B", "2026-01-01T15:00:00Z", quant_packet(),
        mode="HISTORICAL_BAYESIAN", prior_packet=prior_packet(), context_updates=context, draws=500,
        allow_test_calibration=True,
    )
    assert out["score_engine_mode"] == "HISTORICAL_BAYESIAN"
    assert out["posterior"]["context_audit"]["updates_applied"][0]["source_group"] == "LINEUP"


def test_uncertainty_only_keeps_mean_and_inflates_covariance():
    mu = np.array([0.1, -0.1]); cov = np.eye(2) * 0.1
    post_mu, post_cov, applied = apply_validated_context_updates(mu, cov, [{
        "source_group": "SCHEDULE", "validated": True, "effect_mode": "UNCERTAINTY_ONLY",
        "cov_inflation": [[0.2, 0.0], [0.0, 0.1]], "absorbed_fraction": 0.0,
    }])
    assert post_mu == pytest.approx(mu)
    assert np.diag(post_cov).tolist() == pytest.approx([0.3, 0.2])
    assert applied[0]["status"] == "APPLIED"


def test_overlap_and_absorption_remove_quantified_effect():
    mu = np.array([0.0, 0.0]); cov = np.eye(2)
    update = {"source_group": "RECENT_FORM", "validated": True, "effect_mode": "QUANTIFIED_OBSERVATION",
              "mean_log_lambda": [1.0, 1.0], "cov_log_lambda": [[0.1, 0], [0, 0.1]],
              "absorbed_fraction": 1.0, "historical_overlap_fraction": 0.0}
    out, out_cov, _ = apply_validated_context_updates(mu, cov, [update])
    assert out == pytest.approx(mu); assert out_cov == pytest.approx(cov)
    update["absorbed_fraction"] = 0.0; update["historical_overlap_fraction"] = 1.0
    out, _, _ = apply_validated_context_updates(mu, cov, [update])
    assert out == pytest.approx(mu)


def test_invalid_covariance_and_fraction_are_rejected():
    with pytest.raises(BayesianScoreError):
        apply_validated_context_updates(np.zeros(2), np.eye(2), [{
            "source_group": "SCHEDULE", "validated": True, "effect_mode": "UNCERTAINTY_ONLY",
            "cov_inflation": [[1, 2], [2, 1]],
        }])
    out, _, applied = apply_validated_context_updates(np.zeros(2), np.eye(2), [{
        "source_group": "RECENT_FORM", "validated": True, "mean_log_lambda": [1, 1],
        "cov_log_lambda": np.eye(2).tolist(), "absorbed_fraction": 0.2, "effective_fraction": 1.0,
    }])
    assert out == pytest.approx(np.zeros(2))
    assert applied[0]["status"] == "REJECTED_UNCALIBRATED"


@pytest.mark.parametrize("payload", [
    {"actual_score": "2-1"}, {"nested": {"future_result": "1-0"}},
    {"post_kickoff": True},
])
def test_recursive_leakage_fields_are_blocked(payload):
    with pytest.raises(PrematchContextError, match="PREMATCH_LEAKAGE_FIELD"):
        validate_prematch_context_payload(payload, kickoff="2026-01-01T15:00:00Z")


def test_timestamp_and_lineup_gates():
    with pytest.raises(PrematchContextError, match="EVIDENCE_AFTER_CONTEXT_SNAPSHOT"):
        validate_prematch_context_payload({"evidence_timestamp": "2026-01-01T16:00:00Z"}, kickoff="2026-01-01T17:00:00Z", context_snapshot_timestamp="2026-01-01T15:00:00Z")
    with pytest.raises(PrematchContextError, match="LINEUP_AFTER_CONTEXT_SNAPSHOT"):
        validate_prematch_context_payload({"lineup_timestamp": "2026-01-01T13:00:00Z"}, context_snapshot_timestamp="2026-01-01T12:00:00Z", kickoff="2026-01-01T15:00:00Z")


def test_historical_pre_match_fields_are_allowed():
    payload = {
        "historical_goals": [1, 2], "goals_last_5": [1, 0, 2, 1, 1],
        "expected_goals": 1.4, "previous_match_result": "W", "past_scores": ["1-0"],
        "xg": 1.2, "xga": 0.8, "source_match_timestamp": "2025-12-31T15:00:00Z",
    }
    result = validate_prematch_context_payload(payload, kickoff="2026-01-01T15:00:00Z")
    assert result["status"] == "VALIDATED_PREMATCH_PAYLOAD"


def test_market_snapshot_mismatch_is_allowed_but_explicitly_flagged():
    result = validate_prematch_context_payload(
        {"source_group": "SCHEDULE", "evidence_timestamp": "2026-01-01T13:00:00Z"},
        kickoff="2026-01-01T15:00:00Z", context_snapshot_timestamp="2026-01-01T14:00:00Z",
        market_snapshot_timestamp="2026-01-01T12:00:00Z",
    )
    assert result["market_context_time_mismatch"] is True
    assert result["market_absorption_status"] == "INFORMATION_NEWER_THAN_MARKET_SNAPSHOT"


def test_quantified_calibration_gate_and_test_only_runtime_gate():
    raw = {
        "source_group": "RECENT_FORM", "validated": True, "effect_mode": "QUANTIFIED_OBSERVATION",
        "mean_log_lambda": [1.0, 1.0], "cov_log_lambda": np.eye(2).tolist(),
        "calibration_ref": "abc", "calibration_status": "TEST_ONLY", "calibration_version": "v1",
        "evidence_timestamp": "2026-01-01T10:00:00Z", "context_snapshot_timestamp": "2026-01-01T12:00:00Z",
        "provenance": {"source": "test"},
    }
    mu, _, applied = apply_validated_context_updates(np.zeros(2), np.eye(2), [raw])
    assert mu == pytest.approx(np.zeros(2))
    assert applied[0]["status"] == "REJECTED_UNCALIBRATED"
    mu, _, applied = apply_validated_context_updates(np.zeros(2), np.eye(2), [raw], allow_test_calibration=True)
    assert mu[0] > 0.0 and applied[0]["status"] == "APPLIED"


def test_historical_overlap_is_fail_safe_but_market_only_is_not_overconstrained():
    raw = {
        "source_group": "RECENT_FORM", "validated": True, "effect_mode": "QUANTIFIED_OBSERVATION",
        "mean_log_lambda": [1.0, 1.0], "cov_log_lambda": np.eye(2).tolist(),
        "calibration_ref": "abc", "calibration_status": "APPROVED_TRAIN_ONLY", "calibration_version": "v1",
        "evidence_timestamp": "2026-01-01T10:00:00Z", "context_snapshot_timestamp": "2026-01-01T12:00:00Z",
        "provenance": {"source": "train"},
    }
    mu, _, applied = apply_validated_context_updates(np.zeros(2), np.eye(2), [raw], score_engine_mode="HISTORICAL_BAYESIAN")
    assert mu == pytest.approx(np.zeros(2))
    assert applied[0]["status"] == "REJECTED_UNKNOWN_HISTORICAL_OVERLAP"
    mu, _, applied = apply_validated_context_updates(np.zeros(2), np.eye(2), [raw], score_engine_mode="MARKET_ONLY_FORMAL")
    assert mu[0] > 0.0 and applied[0]["status"] == "APPLIED"


def test_default_real_titan_context_is_non_blocking_and_no_mean_shift():
    packet = build_prematch_context_updates(kickoff="2026-01-01T15:00:00Z")
    assert packet["real_titan_calibration"] == "NONE_RESULT_ONLY_DATASET"
    assert set(packet["source_status"].values()) == {"INSUFFICIENT_DATA"}
    base = build_formal_market_score_packet(quant_packet(), draws=500)
    out = build_formal_market_score_packet(quant_packet(), context_updates=packet, draws=500)
    assert out["lambda_home"] == pytest.approx(base["lambda_home"])
    assert out["lambda_away"] == pytest.approx(base["lambda_away"])


def test_context_cannot_reintroduce_market_source_groups():
    with pytest.raises(BayesianScoreError, match="Unknown source_group"):
        apply_validated_context_updates(np.zeros(2), np.eye(2), [{
            "source_group": "1X2", "validated": True, "mean_log_lambda": [0, 0], "cov_log_lambda": np.eye(2).tolist(),
        }])


def test_historical_path_keeps_audit_and_context_is_not_team_goal_baseline():
    out = resolve_score_engine("UCL", "2025-26", "A", "B", "2026-01-01T15:00:00Z", quant_packet(), mode="MARKET_ONLY_FORMAL", draws=500)
    assert out["score_engine_mode"] == "MARKET_ONLY_FORMAL"
    assert out.get("team_goal_baseline_audit", {}).get("formal_model_1_weight_impact", "NONE") == "NONE"
