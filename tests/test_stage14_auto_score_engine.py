import pytest

from gpt.model_1_packet_bridge import build_production_correct_score_evidence
from gpt.stage14_auto import prior_usefulness_gate, resolve_score_engine


def quant():
    return {
        "match_id": "formal-1",
        "reconstruction": {
            "Pinnacle": {"lambda_home": 2.20, "lambda_away": .90, "rho": -.05, "max_abs_residual": .004},
            "Bet365": {"lambda_home": 2.10, "lambda_away": .95, "rho": -.04, "max_abs_residual": .005},
            "Macau": {"lambda_home": 2.25, "lambda_away": .88, "rho": -.06, "max_abs_residual": .006},
        },
    }


def prior(activation="ACTIVE"):
    return {
        "status": "VALID", "activation": activation,
        "mean_log_lambda": [.72, -.05],
        "cov_log_lambda": [[.10, .01], [.01, .10]],
        "source_groups": ["TEAM_DATA"], "calibration_ref": "unit",
    }


def call(**kwargs):
    return resolve_score_engine(
        "英超", "2026-27", "A", "B", "2026-08-15", quant(),
        draws=500, **kwargs,
    )


@pytest.mark.parametrize("activation", ["SHADOW", "DISABLED", "INSUFFICIENT_HISTORY"])
def test_auto_non_active_prior_routes_formal_market(activation):
    result=call(mode="AUTO",prior_store={"competition_status":{"英超":{"activation":activation}}})
    assert result["status"]=="FORMAL_SCORE_TOP3"
    assert result["score_engine_mode"]=="MARKET_ONLY_FORMAL"
    assert result["prior_used"] is False
    assert result["historical_prior_activation"]==activation
    assert result["historical_prior"] is None
    assert result["market_cluster_used"] is True
    assert result["market_companies_used"]==["Pinnacle","Bet365","Macau"]
    assert result["no_fake_historical_prior"] is True
    assert all(result[f"Top{i}"] is not None for i in (1,2,3))


def test_auto_active_explicit_prior_routes_historical_bayesian():
    result=call(mode="AUTO",prior_packet=prior())
    assert result["status"]=="BAYESIAN_POSTERIOR_TOP3"
    assert result["score_engine_mode"]=="HISTORICAL_BAYESIAN"
    assert result["prior_used"] is True
    assert result["historical_prior_activation"]=="ACTIVE"
    assert result["posterior"]["rho_source"] in {"VALIDATED_HISTORICAL_PRIOR","CORE_MARKET_RECONSTRUCTION_MEDIAN"}


def test_auto_active_but_missing_model_falls_back_to_formal_market():
    store={"status":"VALID","competition_status":{"英超":{"activation":"ACTIVE"}},"competition_models":{}}
    result=call(mode="AUTO",prior_store=store)
    assert result["score_engine_mode"]=="MARKET_ONLY_FORMAL"
    assert result["prior_used"] is False
    assert result["historical_prior_resolution_error"]


def test_auto_missing_market_cluster_is_missing():
    result=resolve_score_engine("英超","2026-27","A","B","2026-08-15",
                                {"match_id":"empty","reconstruction":{}},draws=500)
    assert result["status"]=="MISSING"
    assert result["reason"]=="MISSING_CORE_MARKET"


def test_explicit_historical_mode_requires_prior_and_never_falls_back():
    result=call(mode="HISTORICAL_BAYESIAN")
    assert result["status"]=="MISSING"
    assert result["reason"]=="BAYESIAN_PRIOR_REQUIRED"
    assert result["no_market_only_fallback"] is True
    shadow=call(mode="HISTORICAL_BAYESIAN",prior_packet=prior("SHADOW"))
    assert shadow["status"]=="MISSING"
    assert shadow["reason"]=="BAYESIAN_PRIOR_UNAVAILABLE"


def test_explicit_prior_api_remains_compatible():
    result=call(mode="HISTORICAL_BAYESIAN",prior_packet=prior())
    assert result["score_engine_mode"]=="HISTORICAL_BAYESIAN"
    assert result["prior_used"] is True


def test_market_cluster_is_one_correlated_likelihood_not_votes():
    result=call(mode="MARKET_ONLY_FORMAL")
    market=result["score_distribution"]["market_likelihood"]
    assert market["method"]=="CORRELATED_MARKET_CLUSTER_LOG_RATE"
    assert market["not_independent_votes"] is True
    assert result["anti_double_counting"]["independent_bookmaker_votes"] is False


@pytest.mark.parametrize("mode,prior_packet",[("MARKET_ONLY_FORMAL",None),("HISTORICAL_BAYESIAN",prior())])
def test_same_positive_ah_gate_applies_to_both_modes(mode,prior_packet):
    result=call(mode=mode,prior_packet=prior_packet,execution_path={
        "winner":"HOME","ah":{"formal":True,"home_handicap":-1.,"backing":"HOME"}})
    assert result["AH_gate_status"]=="APPLIED_POSITIVE_SETTLEMENT_ONLY"
    assert result["raw_top10"]
    assert all(row["ah_payoff"]>0 for row in result["top3"])
    assert any(row["ah_payoff"]==0 for row in result["raw_top10"])


@pytest.mark.parametrize("mode,prior_packet",[("MARKET_ONLY_FORMAL",None),("HISTORICAL_BAYESIAN",prior())])
def test_execution_and_ou_never_mutate_raw_distribution(mode,prior_packet):
    base=call(mode=mode,prior_packet=prior_packet)
    filtered=call(mode=mode,prior_packet=prior_packet,execution_path={
        "winner":"HOME","ah":{"formal":True,"home_handicap":-1.,"backing":"HOME"},
        "ou":{"side":"OVER","line":3.5,"hard_gate":False}})
    assert filtered["mean_log_lambda"]==base["mean_log_lambda"]
    assert filtered["cov_log_lambda"]==base["cov_log_lambda"]
    assert filtered["rho"]==base["rho"]
    assert [(r["score"],r["probability"]) for r in filtered["raw_top10"]]==[
        (r["score"],r["probability"]) for r in base["raw_top10"]]


def test_snapshot_phase_is_explicit_or_truthful_current():
    assert call(mode="MARKET_ONLY_FORMAL")["snapshot_phase"]=="current"
    assert call(mode="MARKET_ONLY_FORMAL",snapshot_phase="opening")["snapshot_phase"]=="opening"
    packet=quant();packet["snapshot_metadata"]={"phase":"closing"}
    result=resolve_score_engine("英超","2026-27","A","B","2026-08-15",packet,draws=500)
    assert result["snapshot_phase"]=="closing"


def test_usefulness_gate_rejects_runtime_target_fields():
    with pytest.raises(ValueError,match="actual_score"):
        prior_usefulness_gate(quant_packet=quant(),historical_prior_activation="ACTIVE",
                              prior_packet=prior(),snapshot_phase="current",
                              runtime_metadata={"nested":{"actual_score":"2-0"}})
    packet=quant();packet["observed_home_score_after_kickoff"]=2
    with pytest.raises(ValueError,match="home_score"):
        prior_usefulness_gate(quant_packet=packet,historical_prior_activation="ACTIVE",
                              prior_packet=prior(),snapshot_phase="current")


def test_production_bridge_defaults_to_auto_market_formal():
    out=build_production_correct_score_evidence(
        quant_packet=quant(),competition="英超",season="2026-27",home_team="A",away_team="B",
        kickoff="2026-08-15",prior_store={"competition_status":{"英超":{"activation":"SHADOW"}}},draws=500)
    assert out["score_engine_mode"]=="MARKET_ONLY_FORMAL"
    assert len(out["top3_scores"])==3
    assert out["no_fake_historical_prior"] is True
