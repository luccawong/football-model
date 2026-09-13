"""Exercise the committed real-market Stage14 production smoke packets."""
from hashlib import sha256
import json
from pathlib import Path

import pytest

from gpt.prior_engine import PriorEngineError
from gpt.prior_runtime import resolve_prior
from gpt.quant_core import build_quant_packet
from gpt.stage14_auto import resolve_score_engine


ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "database/priors/model_1_titan_prior_store.json"
SMOKE = ROOT / "docs/data/stage14_production_smoke.json"
DOMESTIC = {"英超", "西甲", "意甲", "德甲", "法甲"}


def _artifact():
    return json.loads(SMOKE.read_text(encoding="utf-8"))


def test_active_ucl_runtime_model_is_checked_and_loadable():
    store = json.loads(STORE.read_text(encoding="utf-8"))
    assert store["competition_status"]["欧冠"]["activation"] == "ACTIVE"
    ref = store["model_files"]["欧冠"]
    raw = (STORE.parent / ref["path"]).read_bytes()
    assert sha256(raw).hexdigest() == ref["sha256"]
    payload = json.loads(raw)
    assert payload["provenance"]["test_recalibration_performed"] is False
    assert payload["provenance"]["process_covariance_source"] == "FROZEN_TRAIN_ONLY_MANIFEST"
    assert payload["provenance"]["market_inputs_used"] is False
    model = payload["model"]
    teams = [state["team"] for state in model["states"] if state["season_start"] == 2025]
    prior = resolve_prior(
        {
            "competition": "欧冠",
            "season": "2026-27",
            "home_team": teams[0],
            "away_team": teams[1],
            "kickoff": "2026-08-01",
        },
        STORE,
    )
    assert prior["status"] == "VALID"
    assert prior["activation"] == "ACTIVE"
    assert prior["anti_double_counting"]["market_inputs_used"] is False
    assert prior["anti_double_counting"]["process_covariance_train_only"] is True
    with pytest.raises(PriorEngineError, match="later than the requested fixture"):
        resolve_prior(
            {
                "competition": "欧冠",
                "season": "2025-2026",
                "home_team": teams[0],
                "away_team": teams[1],
                "kickoff": "2025-07-08 23:00",
            },
            STORE,
        )


@pytest.mark.parametrize("case", _artifact()["cases"], ids=lambda row: row["competition"])
def test_real_archived_market_packet_produces_formal_top3(case):
    forbidden = {"home_score", "away_score", "actual_score", "actual_result"}
    assert forbidden.isdisjoint(case)
    assert forbidden.isdisjoint(case["market_payload"])
    quant = build_quant_packet(case["market_payload"])
    actual = resolve_score_engine(
        case["competition"],
        case["season"],
        case["home_team"],
        case["away_team"],
        case["kickoff"],
        quant,
        snapshot_phase=case["snapshot_phase"],
        mode="AUTO",
        prior_store=STORE,
        prior_packet=case.get("historical_prior_packet"),
        execution_path=case["formal_execution_path"],
        draws=_artifact()["draws"],
    )
    expected = case["result"]
    expected_mode = "MARKET_ONLY_FORMAL" if case["competition"] in DOMESTIC else "HISTORICAL_BAYESIAN"
    assert actual["score_engine_mode"] == expected_mode == expected["score_engine_mode"]
    assert actual["prior_used"] is (case["competition"] == "欧冠")
    assert actual["AH_gate_status"] == "APPLIED_POSITIVE_SETTLEMENT_ONLY"
    assert [actual[f"Top{i}"]["score"] for i in (1, 2, 3)] == [
        expected[f"Top{i}"]["score"] for i in (1, 2, 3)
    ]
    assert all(row["ah_payoff"] > 0.0 for row in actual["execution_filtered_top3"])
    assert actual["no_fake_historical_prior"] is True
    assert actual["anti_double_counting"]["market_cluster_is_one_correlated_likelihood"] is True
    assert case["historical_prior_state_not_later_than_kickoff"] is True


def test_smoke_artifact_is_result_blind_and_complete():
    artifact = _artifact()
    assert artifact["routing_smoke_not_historical_accuracy_evaluation"] is True
    assert set(artifact["result_fields_excluded"]) == {
        "home_score", "away_score", "actual_score", "actual_result"
    }
    assert {row["competition"] for row in artifact["cases"]} == DOMESTIC | {"欧冠"}
