"""GPT Football Full-Stack evidence utilities v1.0.0.

Deterministic QC, uncertainty, lifecycle and evaluation helpers.
This module never issues betting recommendations and never converts qualitative
context into unvalidated probability adjustments.
"""
from __future__ import annotations
from math import log
from typing import Mapping, Sequence, Any, Dict
import numpy as np

FEATURE_ENGINE_VERSION = "GPT-FEATURE-1.0.0"

class FeatureInputError(ValueError):
    pass

def _prob3(p: Sequence[float]) -> np.ndarray:
    a=np.asarray(p,dtype=float)
    if a.shape != (3,) or not np.all(np.isfinite(a)) or np.any(a<0):
        raise FeatureInputError("Expected three finite non-negative probabilities.")
    s=float(a.sum())
    if s <= 0:
        raise FeatureInputError("Probability mass must be positive.")
    return a/s

def entropy_1x2(p: Sequence[float]) -> float:
    a=_prob3(p)
    return float(-sum(x*log(x) for x in a if x>0))

def normalized_entropy_1x2(p: Sequence[float]) -> float:
    return entropy_1x2(p)/log(3.0)

def ensemble_disagreement(predictions: Mapping[str, Sequence[float]]) -> Dict[str, Any]:
    if not predictions:
        raise FeatureInputError("At least one model prediction is required.")
    names=list(predictions)
    mat=np.vstack([_prob3(predictions[n]) for n in names])
    mean=mat.mean(axis=0)
    return {
        "models": names,
        "mean": {"home":float(mean[0]),"draw":float(mean[1]),"away":float(mean[2])},
        "std_pp": {"home":float(mat[:,0].std()*100),"draw":float(mat[:,1].std()*100),"away":float(mat[:,2].std()*100)},
        "range_pp": {"home":float((mat[:,0].max()-mat[:,0].min())*100),"draw":float((mat[:,1].max()-mat[:,1].min())*100),"away":float((mat[:,2].max()-mat[:,2].min())*100)},
        "mean_normalized_entropy": normalized_entropy_1x2(mean),
    }

def brier_1x2(p: Sequence[float], outcome: int) -> float:
    a=_prob3(p)
    if outcome not in (0,1,2): raise FeatureInputError("outcome must be 0=home,1=draw,2=away.")
    y=np.zeros(3); y[outcome]=1.0
    return float(np.mean((a-y)**2))

def log_loss_1x2(p: Sequence[float], outcome: int, eps: float=1e-15) -> float:
    a=_prob3(p)
    if outcome not in (0,1,2): raise FeatureInputError("outcome must be 0=home,1=draw,2=away.")
    return float(-log(max(float(a[outcome]),eps)))

def rps_1x2(p: Sequence[float], outcome: int) -> float:
    a=_prob3(p)
    if outcome not in (0,1,2): raise FeatureInputError("outcome must be 0=home,1=draw,2=away.")
    y=np.zeros(3); y[outcome]=1.0
    return float(((np.cumsum(a)[:-1]-np.cumsum(y)[:-1])**2).sum()/2.0)

def calibration_bins(probabilities, outcomes, bins: int=10) -> Dict[str, Any]:
    p=np.asarray(probabilities,dtype=float); y=np.asarray(outcomes,dtype=int)
    if p.ndim!=1 or y.ndim!=1 or len(p)!=len(y) or len(p)==0: raise FeatureInputError("invalid calibration vectors")
    if np.any(~np.isfinite(p)) or np.any((p<0)|(p>1)) or np.any((y<0)|(y>1)): raise FeatureInputError("invalid binary inputs")
    edges=np.linspace(0,1,bins+1); rows=[]; ece=0.0
    for i in range(bins):
        lo,hi=edges[i],edges[i+1]
        mask=(p>=lo)&((p<hi) if i<bins-1 else (p<=hi))
        n=int(mask.sum())
        if not n: continue
        mp=float(p[mask].mean()); oy=float(y[mask].mean())
        ece += (n/len(p))*abs(mp-oy)
        rows.append({"lo":float(lo),"hi":float(hi),"n":n,"mean_pred":mp,"observed":oy})
    return {"ece":float(ece),"bins":rows}

def ah_lifecycle(events) -> Dict[str, Any]:
    if len(events)<1: raise FeatureInputError("At least one AH event is required.")
    lines=np.array([float(e["line"]) for e in events],dtype=float)
    if np.any(~np.isfinite(lines)): raise FeatureInputError("AH lines must be finite.")
    deltas=np.diff(lines); signs=np.sign(deltas[deltas!=0])
    reversals=int(np.sum(signs[1:]!=signs[:-1])) if len(signs)>1 else 0
    opening=float(lines[0]); current=float(lines[-1]); deepest=float(lines.min()); shallowest=float(lines.max())
    return {"opening_line":opening,"current_line":current,"deepest_home_line":deepest,"shallowest_home_line":shallowest,"net_home_depth_goals":float(opening-current),"reversals":reversals,"failed_upgrade":bool(current-deepest>=0.25-1e-9),"failed_downgrade":bool(shallowest-current>=0.25-1e-9)}

def probability_lifecycle(probabilities) -> Dict[str, Any]:
    p=np.asarray(probabilities,dtype=float)
    if len(p)<1 or np.any(~np.isfinite(p)) or np.any((p<=0)|(p>=1)): raise FeatureInputError("Probabilities must lie in (0,1).")
    d=np.diff(p); signs=np.sign(d[d!=0]); reversals=int(np.sum(signs[1:]!=signs[:-1])) if len(signs)>1 else 0
    max_i=int(np.argmax(p)); min_i=int(np.argmin(p))
    return {"opening":float(p[0]),"current":float(p[-1]),"net_pp":float((p[-1]-p[0])*100),"max":float(p[max_i]),"max_index":max_i,"min":float(p[min_i]),"min_index":min_i,"reversals":reversals,"late_reversal_from_peak_pp":float((p[-1]-p[max_i])*100),"late_reversal_from_trough_pp":float((p[-1]-p[min_i])*100)}

def source_freshness(age_hours: float, hard_max_hours: float, soft_max_hours: float|None=None) -> Dict[str, Any]:
    age=float(age_hours); hard=float(hard_max_hours); soft=float(soft_max_hours if soft_max_hours is not None else hard/2)
    if age<0 or hard<=0 or soft<=0 or soft>hard: raise FeatureInputError("Freshness thresholds are invalid.")
    status="FRESH" if age<=soft else ("STALE_WARNING" if age<=hard else "STALE_BLOCK")
    return {"age_hours":age,"soft_max_hours":soft,"hard_max_hours":hard,"status":status}

def module_gate(records: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    allowed={"ACTIVE","PARTIAL","MISSING","STALE","CONFLICT","RESEARCH_ONLY"}; detail={}; hard_block=False
    for name,raw in records.items():
        status=str(raw.get("status","MISSING")).upper(); critical=bool(raw.get("critical",False))
        if status not in allowed: raise FeatureInputError(f"Unknown module status {status} for {name}.")
        if critical and status in {"MISSING","STALE","CONFLICT"}: hard_block=True
        detail[name]={"status":status,"critical":critical}
    return {"hard_block":hard_block,"modules":detail}

def schedule_pressure(rest_days: float|None, next_high_priority_days: float|None, travel_km: float|None=None) -> Dict[str, Any]:
    flags=[]
    if rest_days is not None:
        if rest_days<3: flags.append("SHORT_REST_SEVERE")
        elif rest_days<4: flags.append("SHORT_REST")
    if next_high_priority_days is not None:
        if next_high_priority_days<=3: flags.append("HIGH_PRIORITY_NEXT_3D")
        elif next_high_priority_days<=5: flags.append("HIGH_PRIORITY_NEXT_5D")
    if travel_km is not None and travel_km>=2500: flags.append("LONG_TRAVEL")
    return {"rest_days":rest_days,"next_high_priority_days":next_high_priority_days,"travel_km":travel_km,"flags":flags,"probability_adjustment":None,"note":"Context flag only; do not convert to goals/probability without league-calibrated evidence."}
