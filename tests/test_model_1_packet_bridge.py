import pytest

from gpt.model_1_packet_bridge import (
    PacketBridgeError,
    build_correct_score_quant_evidence,
    build_feature_packet,
    build_runtime_packet,
)


def _quant_packet():
    return {
        "engine_version": "q",
        "match_id": "m2",
        "snapshot_time": "t",
        "reconstruction": {
            "Pinnacle": {"lambda_home": 2.2, "lambda_away": 0.9, "rho": -0.05, "max_abs_residual": 0.004},
            "Bet365": {"lambda_home": 2.1, "lambda_away": 0.95, "rho": -0.04, "max_abs_residual": 0.005},
            "Macau": {"lambda_home": 2.25, "lambda_away": 0.88, "rho": -0.06, "max_abs_residual": 0.006},
        },
    }


def _prior_packet():
    return {
        "status": "VALID",
        "mean_log_lambda": [0.72, -0.05],
        "cov_log_lambda": [[0.10, 0.01], [0.01, 0.10]],
        "source_groups": ["TEAM_DATA"],
        "calibration_ref": "unit-test",
    }


def test_feature_packet_preserves_missing_and_conflicts():
    packet = build_feature_packet(
        match_id="m1",
        module_records={
            "snapshot_qc": {"status": "ACTIVE", "critical": True},
            "weather_pitch": {"status": "MISSING", "critical": False},
        },
        stage_status={"market_snapshot": "COMPLETE", "off_field_weather": "COMPLETE_WITH_MISSING"},
        missing_core_timelines=["William Hill"],
        source_conflicts=["lineup source conflict"],
    )
    assert packet["model_id"] == "MODEL_1"
    assert packet["missing_core_timelines"] == ["William Hill"]
    assert packet["missing_is_negative_evidence"] is False


def test_correct_score_bridge_refuses_market_only_fallback():
    with pytest.raises(PacketBridgeError, match="prior_packet"):
        build_correct_score_quant_evidence(
            quant_packet=_quant_packet(),
            company="Pinnacle",
            bayesian_context_update={"lineup": "neutral"},
            final_top3=["2-0", "2-1", "3-0"],
            direction_consistency_gate=True,
        )


def test_correct_score_bridge_outputs_posterior_top3_and_tail():
    out = build_correct_score_quant_evidence(
        quant_packet=_quant_packet(),
        prior_packet=_prior_packet(),
        execution_path={
            "winner": "HOME",
            "ah": {"backing": "HOME", "home_handicap": -0.5, "hard_gate": True},
            "ou": {"side": "OVER", "line": 2.5, "hard_gate": False},
        },
        draws=500,
    )
    assert out["formal_stage"] == "correct_score_poisson_dixon_coles_bayesian"
    assert out["no_market_only_fallback"] is True
    assert out["score_grid_ref"]["any_team_five_plus_tail"] >= 0
    assert 1 <= len(out["top3_scores"]) <= 3
    assert all(int(score.split("-")[0]) > int(score.split("-")[1]) for score in out["top3_scores"])


def test_runtime_packet_keeps_missing_explicit():
    packet = build_runtime_packet(match_id="m3", quant_packet=None, feature_packet=None, formal_trace=None)
    assert packet["quant_packet"]["status"] == "MISSING"
    assert packet["feature_packet"]["status"] == "MISSING"
    assert packet["formal_trace"]["status"] == "MISSING"
