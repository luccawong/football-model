from datetime import datetime, timedelta
import json

import pytest

from gpt.recent_form import (
    ARTIFACT_VERSION, RecentFormError, RecentFormFeatureBuilder, RecentMatch,
    build_approved_recent_form_context_updates, canonical_json_sha256,
    load_approved_recent_form_artifact, recent_form_observation,
)


def _match(mid, day, home, away, hg, ag):
    return RecentMatch(str(mid), datetime(2024, 8, 1) + timedelta(days=day), "英超", 2024, home, away, hg, ag)


def test_features_are_strictly_before_target_and_same_kickoff_isolated():
    builder = RecentFormFeatureBuilder(window=5, half_life_days=45, shrinkage_matches=4)
    first = _match(1, 0, "A", "B", 4, 0)
    same_kickoff = _match(2, 7, "A", "C", 9, 0)
    target = _match(3, 7, "B", "D", 0, 0)
    later = _match(4, 14, "A", "D", 0, 0)
    features = builder.transform([first, same_kickoff, target, later])
    assert features["2"]["source_match_kickoff_rule"] == "source_match_kickoff < target_match_kickoff"
    # Match 2 is not eligible to inform match 3 despite an adjacent input
    # position because their kickoffs are identical.
    assert features["3"]["effective_samples"]["home"] > 0
    assert features["3"]["effective_samples"]["home"] < 2
    assert features["4"]["effective_samples"]["home"] > features["2"]["effective_samples"]["home"]


def _artifact(activation="APPROVED_PRODUCTION"):
    value = {
        "artifact_version": ARTIFACT_VERSION, "competition": "英超", "market_phase": "OPENING",
        "activation": activation, "runtime_eligible": activation == "APPROVED_PRODUCTION",
        "coefficients": [0.1, 0.2, 0.3, 0.4], "response_coefficients": [[0.1, 0, 0, 0], [0, 0, 0.1, 0]],
        "intercept": [0.0, 0.0], "robust_scaler": {"center": [0, 0, 0, 0], "scale": [1, 1, 1, 1], "fit_scope": "TRAIN_ONLY_MEDIAN_MAD"},
        "cov_log_lambda": [[0.2, 0.0], [0.0, 0.2]],
        "calibration_ref": "test", "calibration_version": "v1",
    }
    value["artifact_sha256"] = canonical_json_sha256(value)
    return value


def test_only_approved_artifact_is_runtime_loadable(tmp_path):
    root = tmp_path / "recent"; root.mkdir()
    approved = _artifact()
    (root / "英超_opening.json").write_text(json.dumps(approved), encoding="utf-8")
    assert load_approved_recent_form_artifact(root, competition="英超", market_phase="OPENING")["calibration_ref"] == "test"
    shadow = _artifact("SHADOW")
    (root / "英超_opening.json").write_text(json.dumps(shadow), encoding="utf-8")
    assert load_approved_recent_form_artifact(root, competition="英超", market_phase="OPENING") is None


def test_observation_is_market_residual_not_a_second_prior():
    artifact = _artifact()
    update = recent_form_observation(
        artifact, {"features": [1, 0, 0, 0]}, evidence_timestamp="2024-08-02T00:00:00Z",
        context_snapshot_timestamp="2024-08-02T00:00:00Z", kickoff="2024-08-03T00:00:00Z",
        base_mean_log_lambda=[0.4, 0.2],
    )
    assert update["mean_log_lambda"] == pytest.approx([0.5, 0.2])
    assert update["historical_overlap_fraction"] == 0.0
    with pytest.raises(RecentFormError, match="NOT_APPROVED"):
        recent_form_observation(_artifact("SHADOW"), {"features": [0, 0, 0, 0]}, evidence_timestamp="2024-08-02T00:00:00Z", context_snapshot_timestamp="2024-08-02T00:00:00Z", kickoff="2024-08-03T00:00:00Z", base_mean_log_lambda=[0.4, 0.2])


def test_prematch_bridge_emits_no_update_for_shadow_artifact(tmp_path):
    root = tmp_path / "recent"; root.mkdir()
    (root / "英超_opening.json").write_text(json.dumps(_artifact("SHADOW")), encoding="utf-8")
    packet = build_approved_recent_form_context_updates(
        artifact_root=root, competition="英超", market_phase="OPENING", feature_row={"features": [1, 0, 0, 0]},
        base_mean_log_lambda=[0.4, 0.2], evidence_timestamp="2024-08-02T00:00:00Z",
        context_snapshot_timestamp="2024-08-02T00:00:00Z", kickoff="2024-08-03T00:00:00Z",
    )
    assert packet["updates"] == []
    assert packet["source_status"]["RECENT_FORM"] == "INSUFFICIENT_DATA"
