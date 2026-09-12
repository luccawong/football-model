"""Release artifact integrity: exercise the actual packaged five-league state."""
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from gpt.domestic_gate import activation_gate
from gpt.prior_engine import PriorEngineError
from gpt.prior_runtime import resolve_prior

ROOT=Path(__file__).resolve().parents[1]
STORE=ROOT/"database/priors/model_1_titan_prior_store.json"


@pytest.mark.parametrize("competition,slug",[("英超","epl"),("西甲","laliga"),("意甲","seriea"),("德甲","bundesliga"),("法甲","ligue1")])
def test_packaged_state_evidence_and_gate(competition,slug):
    store=json.loads(STORE.read_text(encoding="utf-8"))
    ref=store["domestic_v2"][competition]
    raw=(STORE.parent/ref["path"]).read_bytes()
    assert sha256(raw).hexdigest()==ref["sha256"]
    payload=json.loads(raw);frozen=payload["frozen"];oos=payload["oos"]
    cert=ROOT/"docs/data/domestic_prior_v2"/(slug+"_frozen_train.json")
    assert sha256(cert.read_bytes()).hexdigest()==oos["frozen_train_sha256"]
    assert json.loads(cert.read_text(encoding="utf-8"))==frozen
    assert frozen["selected"]["scope"]=="TRAIN_2021_2022_2023_ONLY"
    assert frozen["selected"]["selection_objective"]=="CORRECT_SCORE_PREDICTIVE_NLL"
    gate=activation_gate(oos["validation"],oos["test"],frozen["selected"],frozen["trust"])
    assert gate["activation"]==store["competition_status"][competition]["activation"]=="SHADOW"
    data=json.loads(gzip.decompress((cert.parent/(slug+"_paired.json.gz")).read_bytes()))
    for period in ("validation","test"):
        for phase in ("opening","closing"):
            group=[r for r in data if r["period"]==period and r["phase"]==phase]
            assert len(group)==oos[period][phase]["C"]["n"]
            assert len({r["match_id"] for r in group})==len(group)
            assert all(r["state_cutoff"]<=r["kickoff"] for r in group)
            for model in ("A","B","C"):
                assert np.mean([r["score_nll"][model] for r in group])==pytest.approx(oos[period][phase][model]["correct_score_NLL"])
    teams=payload["model"]["teams"]
    context={"competition":competition,"season":"2026-27","home_team":teams[0],"away_team":teams[1],"kickoff":"2026-08-15"}
    with pytest.raises(PriorEngineError,match="not formally active"):
        resolve_prior(context,STORE)
    research=resolve_prior(context,STORE,require_active=False)
    assert research["activation"]=="SHADOW"
    assert np.linalg.eigvalsh(research["cov_log_lambda"])[0]>0
