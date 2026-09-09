import numpy as np

from gpt.model_1_packet_bridge import (
    build_correct_score_quant_evidence,
    build_feature_packet,
    build_runtime_packet,
)


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


def test_correct_score_bridge_outputs_tail_and_top3():
    quant_packet = {
        "engine_version": "q",
        "match_id": "m2",
        "snapshot_time": "t",
        "reconstruction": {
            "Pinnacle": {"lambda_home": 2.2, "lambda_away": 0.9, "rho": -0.05}
        },
    }
    out = build_correct_score_quant_evidence(
        quant_packet=quant_packet,
        company="Pinnacle",
        bayesian_context_update={"lineup": "neutral"},
        final_top3=["2-0", "2-1", "3-0"],
        direction_consistency_gate=True,
    )
    assert len(out["top3_scores"]) == 3
    assert out["score_grid_ref"]["any_team_five_plus_tail"] >= 0
    assert out["direction_consistency_gate"] is True


def test_runtime_packet_keeps_missing_explicit():
    packet = build_runtime_packet(match_id="m3", quant_packet=None, feature_packet=None, formal_trace=None)
    assert packet["quant_packet"]["status"] == "MISSING"
    assert packet["feature_packet"]["status"] == "MISSING"
    assert packet["formal_trace"]["status"] == "MISSING"
