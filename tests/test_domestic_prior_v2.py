from dataclasses import asdict
from datetime import datetime
import sqlite3

import numpy as np
import pytest

from gpt.domestic_prior import DynamicHyper, dynamic_packet, fit_dynamic
from gpt.prior_engine import PriorEngineError
from scripts.validate_domestic_prior_v2 import (
    Archive, calibrate_trust, estimate_process, estimate_rho, gate, predictive,
    train_rows,
)


def history():
    rng=np.random.default_rng(19)
    rows=[]
    for year in range(2021,2026):
        for month in range(8,13):
            for day in range(1,25):
                home,away=("A","B") if day%2 else ("C","A")
                rows.append({"match_id":f"{year}-{month}-{day}","match_date":datetime(year,month,day),
                    "season":f"{year}-{year+1}","season_start":year,"league":"英超",
                    "home_team":home,"away_team":away,"home_score":int(rng.poisson(1.7)),
                    "away_score":int(rng.poisson(1.1))})
    return rows


@pytest.mark.parametrize("structure",["monthly","rolling30","rolling60","rolling90"])
def test_dynamic_state_ignores_future_and_market_fields(structure):
    rows=history();h=DynamicHyper(structure=structure)
    cutoff=datetime(2023,10,1)
    model=fit_dynamic(rows,"英超",cutoff,h)
    altered=[dict(r,home_score=99,away_score=88) if r["match_date"]>=cutoff else dict(r,odds=999) for r in rows]
    other=fit_dynamic(altered,"英超",cutoff,h)
    assert model==other
    packet=dynamic_packet(model,"A","B","2023-24",cutoff)
    cov=np.array(packet["cov_log_lambda"])
    assert np.allclose(cov,cov.T) and np.linalg.eigvalsh(cov)[0]>0


def test_future_state_is_rejected():
    m=fit_dynamic(history(),"英超",datetime(2024,1,1),DynamicHyper())
    with pytest.raises(PriorEngineError,match="future"):
        dynamic_packet(m,"A","B","2023-24",datetime(2023,9,1))


def test_new_team_fallback_and_learned_class():
    m=fit_dynamic(history(),"英超",datetime(2024,1,1),DynamicHyper())
    p=dynamic_packet(m,"NEW","A","2024-25",datetime(2024,8,1))
    assert p["hierarchy"]["home_team_fallback"]=="COMPETITION_MEAN_PLUS_CURRENT_EVIDENCE"
    m["promoted_class"]={"status":"ESTIMATED","mean":[-.2,-.1],"covariance":[[.08,.01],[.01,.09]]}
    q=dynamic_packet(m,"NEW","A","2024-25",datetime(2024,8,1))
    assert q["hierarchy"]["home_team_fallback"]=="PROMOTED_CLASS"
    assert q["mean_log_lambda"]!=p["mean_log_lambda"]


def test_process_and_inflation_preserve_mean_and_covariance_components():
    m=fit_dynamic(history(),"英超",datetime(2024,1,1),DynamicHyper())
    a=dynamic_packet(m,"A","B","2024-25",datetime(2024,8,1))
    cal={"rho":-.04,"kappa":3.,"process_covariance":[[.1,.01],[.01,.08]],"ref":"train"}
    b=dynamic_packet(m,"A","B","2024-25",datetime(2024,8,1),cal)
    assert a["mean_log_lambda"]==b["mean_log_lambda"]
    assert np.allclose(b["cov_log_lambda"],3*(np.array(a["cov_log_lambda"])+cal["process_covariance"]))
    assert b["rho_prior"]["mean"]==-.04


def test_calibration_rejects_test_records():
    bad=[{"season_start":2025}]
    for fn in (estimate_rho,estimate_process):
        with pytest.raises(PriorEngineError,match="Train"):
            fn(bad)
    with pytest.raises(PriorEngineError,match="Train"):
        calibrate_trust(bad,{},-.03)
    assert {r["season_start"] for r in train_rows(history())}=={2021,2022,2023}


def test_rho_is_estimated_from_actual_scores():
    records=[{"season_start":2022,"mean":[.3,.1],"cov":[[.02,0],[0,.02]],"y":[0,0]} for _ in range(50)]
    assert estimate_rho(records)<-.01
    records=[dict(r,y=[0,1]) for r in records]
    assert estimate_rho(records)>0


def test_predictive_integrates_covariance_and_matches_conditional_limit():
    from gpt.quant_core import score_grid
    mu=np.log([1.6,1.1]);cov=np.eye(2)*1e-10
    g=predictive(mu,cov,-.04)
    assert np.allclose(g,score_grid(1.6,1.1,-.04),atol=1e-8)
    assert not np.allclose(g,predictive(mu,np.eye(2)*.2,-.04))
    assert predictive(mu,np.eye(2)*.2,-.04).sum()==pytest.approx(1.)


def test_opening_closing_never_mix():
    archive=Archive.__new__(Archive)
    archive.tables={"european_odds":{("1","177"):{"opening_home":2,"opening_draw":3,"opening_away":4,
                      "closing_home":1.5,"closing_draw":4,"closing_away":6}},
                    "over_under_odds":{("1","47"):{"opening_line":2.5,"opening_over":.9,"opening_under":.9,
                       "closing_line":3,"closing_over":.8,"closing_under":1.}},
                    "asian_odds":{("1","47"):{"opening_line":.25,"closing_line":.75}}}
    op,ah_o=archive.payload("1","opening");cl,ah_c=archive.payload("1","closing")
    assert op["companies"]["Pinnacle"]["one_x_two"]==[2,3,4]
    assert cl["companies"]["Pinnacle"]["one_x_two"]==[1.5,4,6]
    assert ah_o==-.25 and ah_c==-.75
    archive.tables["european_odds"][("1","177")]["opening_home"]=None
    assert archive.payload("1","opening")[0]["companies"]=={}
    with pytest.raises(ValueError): archive.payload("1","mixed")


def sample_report():
    a={"n":380,"correct_score_NLL":3.,"Top3_coverage":.3,"1X2_Brier":.6,"RPS":.2,
       "OU_over2_5_Brier":.24,"AH_settlement_aware_Brier":.2}
    return {phase:{"A":dict(a),"C":dict(a,correct_score_NLL=2.99)} for phase in ("opening","closing")}


def test_activation_requires_both_seasons_boundary_and_secondary_gates():
    v,t=sample_report(),sample_report();selected={"boundary":[]}
    trust={p:{"boundary":False} for p in v}
    assert gate(v,t,selected,trust)["lifecycle"]=="BOTH_ACTIVE"
    t["closing"]["C"]["correct_score_NLL"]=3.01
    assert gate(v,t,selected,trust)["lifecycle"]=="OPENING_ACTIVE"
    selected["boundary"]=["half_life_days"]
    assert gate(v,t,selected,trust)["activation"]=="SHADOW"
    selected["boundary"]=[]
    v["opening"]["C"]["RPS"]+=.0001
    assert gate(v,t,selected,trust)["activation"]=="SHADOW"


def test_european_models_are_frozen():
    with pytest.raises(PriorEngineError,match="European"):
        fit_dynamic(history(),"欧冠",datetime(2024,1,1),DynamicHyper())


def runtime_store():
    report=sample_report()
    trust={p:{"boundary":False,"kappa":1.,"rho":-.04,
              "process_covariance":[[.01,0],[0,.01]],"ref":"train"} for p in report}
    selected={"boundary":[]}
    model=fit_dynamic(history(),"英超",datetime(2024,1,1),DynamicHyper())
    payload={"competition":"英超","model":model,
             "frozen":{"selected":selected,"trust":trust},
             "oos":{"validation":report,"test":sample_report(),"activation":gate(report,report,selected,trust)}}
    return {"competition_status":{"英超":{"activation":"ACTIVE"}},
            "domestic_v2":{"英超":{"payload":payload}}}


def test_runtime_rechecks_oos_and_phase_not_just_active_label():
    from gpt.prior_runtime import DomesticPriorResolver
    store=runtime_store()
    resolver=DomesticPriorResolver(store,snapshot_phase="opening")
    packet=resolver.resolve_prior("英超","2024-25","A","B","2024-08-01")
    assert packet["activation"]=="ACTIVE"
    store["domestic_v2"]["英超"]["payload"]["oos"]["test"]["opening"]["C"]["correct_score_NLL"]=4.
    with pytest.raises(PriorEngineError,match="OOS evidence"):
        resolver.resolve_prior("英超","2024-25","A","B","2024-08-01")


def test_shadow_is_blocked_in_formal_stage14_even_as_explicit_packet():
    from gpt.stage14_auto import automatic_top3
    from gpt.prior_runtime import resolve_prior
    store=runtime_store()
    store["competition_status"]["英超"]["activation"]="SHADOW"
    context={"competition":"英超","season":"2024-25","home_team":"A","away_team":"B","kickoff":"2024-08-01"}
    result=automatic_top3({},prior_context=context,prior_store=store)
    assert result["reason"]=="BAYESIAN_PRIOR_UNAVAILABLE"
    research=resolve_prior(context,store,require_active=False)
    result=automatic_top3({},prior_packet=research)
    assert result["reason"]=="BAYESIAN_PRIOR_UNAVAILABLE"
    assert result["top3"]==[]


def test_runtime_rejects_current_prices_in_context():
    from gpt.prior_runtime import resolve_prior
    context={"competition":"英超","season":"2024-25","home_team":"A","away_team":"B",
             "kickoff":"2024-08-01","current_1x2":[2,3,4]}
    with pytest.raises(PriorEngineError,match="Forbidden"):
        resolve_prior(context,runtime_store())
