"""Reproducible domestic V2 Train selection and untouched-season OOS audit.

Run with --db <mother sqlite> --out <research directory>. Frozen selection is
written before OOS is read. Test is never passed to calibration functions.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import gammaln
from numpy.polynomial.hermite import hermgauss

from gpt.domestic_prior import DOMESTIC, VERSION, DynamicHyper, fit_dynamic, dynamic_packet, pd
from gpt.prior_engine import PriorEngineError, load_titan_matches
from gpt.prior_competition import file_sha256
from gpt.quant_core import build_quant_packet, score_grid
from gpt.stage14_bayesian import build_market_cluster_likelihood, _normal_update
from scripts.validate_model_1_prior import CORE_IDS, Metrics, _quarter_line

RAW_SHA = "cb409b3ceb882491671c08abbf6815fdfbaa398010de0377ad1d7bcf0d1531a7"
GRID = {"half_life_days": [45.,90.,180.,365.,730.], "team_sd": [.15,.25,.35,.5,.8],
        "transition_sd": [.03,.08,.2,.45,.9]}


def dump(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def train_rows(rows):
    return [r for r in rows if r["season_start"] in (2021,2022,2023)]


def conditional_grid(mean, rho):
    rates = np.exp(np.clip(mean, np.log(.05), np.log(6.)))
    return score_grid(*rates, rho, max_goals=12)


_GH = {}
def predictive(mean, cov, rho, order=12):
    """Deterministic full lognormal integration, matching runtime rate support.

    Tensor Gauss-Hermite avoids comparing different Monte Carlo noise in A/C.
    DC rho's optimization bounds ensure positive cells over [0.05, 6]^2.
    """
    if order not in _GH:
        nodes, weights = hermgauss(order)
        a,b = np.meshgrid(nodes,nodes)
        _GH[order] = (np.column_stack([a.ravel(),b.ravel()])*np.sqrt(2),
                      np.outer(weights,weights).ravel()/np.pi)
    z, w = _GH[order]
    samples = np.exp(np.clip(z @ np.linalg.cholesky(pd(cov)).T + mean, np.log(.05),np.log(6)))
    goals = np.arange(13)
    ph = np.exp(goals*np.log(samples[:,0,None])-samples[:,0,None]-gammaln(goals+1))
    pa = np.exp(goals*np.log(samples[:,1,None])-samples[:,1,None]-gammaln(goals+1))
    grids = ph[:,:,None]*pa[:,None,:]
    grids[:,0,0] *= 1-samples[:,0]*samples[:,1]*rho
    grids[:,0,1] *= 1+samples[:,0]*rho
    grids[:,1,0] *= 1+samples[:,1]*rho
    grids[:,1,1] *= 1-rho
    if np.any(grids < 0):
        raise PriorEngineError("Invalid DC predictive support")
    grids /= grids.sum(axis=(1,2))[:,None,None]
    result = np.einsum("i,ijk->jk",w,grids)
    return result/result.sum()


def _actual_nll(mean, y, rho):
    rates = np.exp(np.clip(mean,np.log(.05),np.log(6)))
    lh,la = rates.T; h,a = y.T
    tau = np.ones(len(y))
    tau[(h==0)&(a==0)] = (1-lh*la*rho)[(h==0)&(a==0)]
    tau[(h==0)&(a==1)] = (1+lh*rho)[(h==0)&(a==1)]
    tau[(h==1)&(a==0)] = (1+la*rho)[(h==1)&(a==0)]
    tau[(h==1)&(a==1)] = 1-rho
    return np.sum(rates-y*np.log(rates)+gammaln(y+1),axis=1)-np.log(tau)


def estimate_rho(records):
    if any(r["season_start"] not in (2021,2022,2023) for r in records):
        raise PriorEngineError("Historical rho accepts Train only")
    mean = np.array([r["mean"] for r in records]); y = np.array([r["y"] for r in records])
    # Predictive support safety limits, never widened using OOS.
    fit = minimize_scalar(lambda rho: float(_actual_nll(mean,y,rho).mean()),
                          bounds=(-.16,.027),method="bounded",options={"xatol":1e-7})
    return float(fit.x)


def estimate_process(records):
    if any(r["season_start"] not in (2021,2022,2023) for r in records):
        raise PriorEngineError("Process covariance accepts Train only")
    rates = np.exp(np.array([r["mean"] for r in records]))
    y = np.array([r["y"] for r in records]); residual = (y-rates)/rates
    empirical = residual.T@residual/len(records)
    noise = np.diag(np.mean(1/rates,axis=0))
    laplace = np.mean([r["cov"] for r in records],axis=0)
    raw = (empirical-noise-laplace); raw=(raw+raw.T)/2
    eig,vec = np.linalg.eigh(raw)
    return ((vec*np.maximum(eig,0))@vec.T).tolist()


def records_for(rows, competition, hyper, seasons, promoted=None):
    target = [r for r in rows if r["league"]==competition and r["season_start"] in seasons]
    models = {}; result=[]
    for r in sorted(target,key=lambda r:(r["match_date"],r["match_id"])):
        # Identical month-start information sets for all four candidate structures.
        cutoff = datetime(r["match_date"].year,r["match_date"].month,1)
        if cutoff not in models:
            models[cutoff] = fit_dynamic(rows,competition,cutoff,hyper,promoted)
        packet = dynamic_packet(models[cutoff],r["home_team"],r["away_team"],r["season"],r["match_date"])
        result.append({"match_id":r["match_id"],"season_start":r["season_start"],
                       "kickoff":r["match_date"].isoformat(),"state_cutoff":cutoff.isoformat(),
                       "mean":packet["mean_log_lambda"],"cov":packet["cov_log_lambda"],
                       "y":[r["home_score"],r["away_score"]]})
    return result


def tune_dynamic(rows, competition, out):
    rows = train_rows(rows)
    evaluated = {}
    def evaluate(h):
        key=json.dumps(asdict(h),sort_keys=True)
        if key in evaluated:
            return evaluated[key]
        records=records_for(rows,competition,h,(2022,2023))
        first=[r for r in records if r["season_start"]==2022]
        second=[r for r in records if r["season_start"]==2023]
        rho=estimate_rho(first)
        # Forward check of rho shrinkage. Zero is a learned candidate, not a constant.
        factors=[0.,.25,.5,.75,1.]
        shrink=min(factors,key=lambda s:np.mean(_actual_nll(np.array([r["mean"] for r in second]),np.array([r["y"] for r in second]),rho*s)))
        final_rho=estimate_rho(records)*shrink
        metric=Metrics()
        for r in records:
            metric.add(conditional_grid(r["mean"],final_rho),*r["y"],None)
        summary=metric.summary()
        evaluated[key]={"hyperparameters":asdict(h),"metrics":summary,"rho":final_rho,"rho_shrinkage":shrink,
                        "rho_first_fold":rho,"selection_objective":"CORRECT_SCORE_PREDICTIVE_NLL"}
        dump(out/"search.json",list(evaluated.values()))
        print(competition,asdict(h),summary["correct_score_NLL"],flush=True)
        return evaluated[key]
    winners=[]
    for structure in ("monthly","rolling30","rolling60","rolling90"):
        h=DynamicHyper(structure=structure)
        evaluate(h)
        # Deterministic coordinate search with two passes. No Test-directed grids.
        for _ in range(2):
            old=h
            for name,values in GRID.items():
                options=[replace(h,**{name:value}) for value in values]
                h=min(options,key=lambda hp:evaluate(hp)["metrics"]["correct_score_NLL"])
            if old==h: break
        winners.append(h)
    winner=min(winners,key=lambda h:evaluate(h)["metrics"]["correct_score_NLL"])
    selected=evaluate(winner)
    # Secondary metrics constrain release, never overtake score NLL selection.
    boundary=[k for k,v in GRID.items() if getattr(winner,k) in (v[0],v[-1])]
    selected={**selected,"boundary":boundary,"scope":"TRAIN_2021_2022_2023_ONLY",
              "folds":[{"fit":[2021],"validate":2022},{"fit":[2021,2022],"validate":2023}],
              "candidate_count":len(evaluated),"structure_winners":[asdict(h) for h in winners]}
    dump(out/"selected_dynamic.json",selected)
    return winner,selected


def estimate_promoted(rows,competition,hyper):
    rows=train_rows(rows); observations=[]; posterior_cov=[]
    for season in (2022,2023):
        old={r[k] for r in rows if r["league"]==competition and r["season_start"]==season-1 for k in ("home_team","away_team")}
        current=[r for r in rows if r["league"]==competition and r["season_start"]==season]
        if not current: continue
        cutoff=max(r["match_date"] for r in current)+timedelta(seconds=1)
        model=fit_dynamic(rows,competition,cutoff,hyper)
        teams=model["teams"]; n=len(teams)
        for team in sorted({r[k] for r in current for k in ("home_team","away_team")}-old):
            idx=[2+teams.index(team),2+n+teams.index(team)]
            observations.append(np.array(model["theta"])[idx]); posterior_cov.append(np.array(model["covariance"])[np.ix_(idx,idx)])
    if len(observations)<6:
        return {"status":"FALLBACK","mean":[0.,0.],"n":len(observations),"reason":"FEWER_THAN_SIX_TRAIN_ENTRANTS"}
    values=np.array(observations); cov=np.cov(values.T)+np.mean(posterior_cov,axis=0)
    # Empirical-Bayes class mean shrinkage based on sampling variance.
    variance=np.diag(cov); strength=hyper.team_sd**2
    mean=values.mean(axis=0)*strength/(strength+variance/len(values))
    return {"status":"ESTIMATED","mean":mean.tolist(),"covariance":pd(cov).tolist(),
            "n":len(values),"scope":"TRAIN_DOMESTIC_ENTRANTS_ONLY"}


class Archive:
    def __init__(self, db):
        con=sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro",uri=True);con.row_factory=sqlite3.Row
        self.tables={}
        for table,kind in (("european_odds","euro"),("over_under_odds","vip"),("asian_odds","vip")):
            ids=[d[kind] for d in CORE_IDS.values()]
            rows=con.execute(f"SELECT * FROM {table} WHERE company_id IN (?,?,?)",ids).fetchall()
            chosen={}
            for row in sorted(rows,key=lambda r:(str(r["match_id"]),str(r["company_id"]),not bool((r["company_raw"] or "").strip()),str(dict(r)))):
                chosen.setdefault((str(row["match_id"]),str(row["company_id"])),dict(row))
            self.tables[table]=chosen
        con.close()

    def payload(self,mid,phase):
        if phase not in ("opening","closing"): raise ValueError("Explicit market phase required")
        companies={}; ah=None
        for name,ids in CORE_IDS.items():
            euro=self.tables["european_odds"].get((mid,ids["euro"]))
            ou=self.tables["over_under_odds"].get((mid,ids["vip"]))
            asian=self.tables["asian_odds"].get((mid,ids["vip"]))
            if ah is None and asian:
                try: ah=-_quarter_line(asian[phase+"_line"])
                except (ValueError,TypeError): pass
            if not euro or not ou: continue
            try:
                prices=[float(euro[phase+"_"+k]) for k in ("home","draw","away")]
                over,under=[1+float(ou[phase+"_"+k]) for k in ("over","under")]
                line=_quarter_line(ou[phase+"_line"])
                if not all(np.isfinite(x) and x>1 for x in prices+[over,under]) or not np.isfinite(line): continue
                companies[name]={"one_x_two":prices,"ou":{"line":line,"over":over,"under":under,"role":"dynamic"}}
            except (ValueError,TypeError): continue
        return {"match_id":mid,"companies":companies},ah


def reconstruct(job):
    mid,phase,payload,ah=job
    if not payload["companies"]: return mid,phase,None
    q=build_quant_packet(payload,{"report_ou_lines":[],"report_ah_lines":[]})
    market=build_market_cluster_likelihood(q)
    if market["status"]!="VALID": return mid,phase,None
    return mid,phase,{"market":market,"ah":ah,"phase":phase}


def markets_for(records,archive,path,workers):
    cache=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    jobs=[]
    for r in records:
        for phase in ("opening","closing"):
            key=r["match_id"]+"|"+phase
            if key not in cache:
                payload,ah=archive.payload(r["match_id"],phase)
                jobs.append((r["match_id"],phase,payload,ah))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i,(mid,phase,value) in enumerate(pool.map(reconstruct,jobs,chunksize=8)):
            cache[mid+"|"+phase]=value
            if (i+1)%100==0:
                dump(path,cache);print("markets",i+1,"/",len(jobs),flush=True)
    dump(path,cache)
    return cache


def calibrate_trust(records,markets,rho):
    if any(r["season_start"] not in (2021,2022,2023) for r in records):
        raise PriorEngineError("Kappa accepts Train only")
    process=np.array(estimate_process(records))
    selected={}
    for phase in ("opening","closing"):
        common=[r for r in records if markets.get(r["match_id"]+"|"+phase)]
        def loss(log_k):
            losses=[]
            for r in common:
                m=markets[r["match_id"]+"|"+phase]["market"]
                mu,cov=_normal_update(np.array(r["mean"]),pd(np.exp(log_k)*(np.array(r["cov"])+process)),
                                      np.array(m["mean_log_lambda"]),np.array(m["cov_log_lambda"]))
                grid=predictive(mu,cov,rho)
                losses.append(-np.log(max(1e-15,grid[tuple(r["y"]) ])))
            return float(np.mean(losses))
        bounds=(np.log(.01),np.log(1000.))
        result=minimize_scalar(loss,bounds=bounds,method="bounded",options={"xatol":.015})
        selected[phase]={"kappa":float(np.exp(result.x)),"objective":float(result.fun),"n":len(common),
                         "boundary":bool(min(result.x-bounds[0],bounds[1]-result.x)<.05),
                         "bounds":[.01,1000.],"scope":"TRAIN_INNER_OOS_CORRECT_SCORE_NLL",
                         "process_covariance":process.tolist(),"rho":rho,"ref":VERSION}
    return selected


def paired(a,c):
    delta=np.array(c)-np.array(a)
    rng=np.random.default_rng(20260912)
    means=np.mean(delta[rng.integers(0,len(delta),size=(5000,len(delta)))],axis=1)
    return {"mean_delta":float(delta.mean()),"median_delta":float(np.median(delta)),
            "bootstrap95":np.quantile(means,[.025,.975]).tolist(),
            "fraction_C_higher_actual_score_probability":float(np.mean(delta<0)),"n":len(delta),
            "bootstrap":"PAIRED_MATCH_5000_SEED_20260912"}


def evaluate(records,markets,calibration):
    result={}; details=[]
    for phase in ("opening","closing"):
        metrics={k:Metrics() for k in ("A","B","C")}
        params=calibration[phase]
        for r in records:
            market=markets.get(r["match_id"]+"|"+phase)
            if not market: continue
            m=market["market"]; lap=np.array(r["cov"]); process=np.array(params["process_covariance"])
            cov=pd(params["kappa"]*(lap+process))
            mu_c,cov_c=_normal_update(np.array(r["mean"]),cov,np.array(m["mean_log_lambda"]),np.array(m["cov_log_lambda"]))
            grids={"A":conditional_grid(m["mean_log_lambda"],m["rho_market_median"]),
                   "B":predictive(r["mean"],lap+process,params["rho"]),
                   "C":predictive(mu_c,cov_c,params["rho"])}
            for name,g in grids.items(): metrics[name].add(g,*r["y"],market["ah"])
            details.append({**r,"phase":phase,"score_nll":{k:metrics[k].score_nll[-1] for k in metrics}})
        result[phase]={k:v.summary() for k,v in metrics.items()}
        result[phase]["paired_C_minus_A"]=paired(metrics["A"].score_nll,metrics["C"].score_nll)
        result[phase]["target_n"]=len(records)
    return result,details


def gate(validation,test,selected,trust):
    from gpt.domestic_gate import activation_gate
    return activation_gate(validation,test,selected,trust)


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--db",required=True);parser.add_argument("--out",required=True)
    parser.add_argument("--competition",choices=DOMESTIC);parser.add_argument("--workers",type=int,default=4)
    args=parser.parse_args();root=Path(args.out);root.mkdir(parents=True,exist_ok=True)
    actual=file_sha256(args.db)
    if actual!=RAW_SHA: raise PriorEngineError("Mother source SHA256 mismatch")
    rows,audit=load_titan_matches(args.db)
    if audit["matches_count"]!=13090: raise PriorEngineError("Raw count mismatch")
    dump(root/"provenance.json",{"sha256":actual,"raw_count":13090,"source":"titan数据库.zip -> football_odds_2021_2026.sqlite"})
    archive=Archive(args.db)
    for comp in ([args.competition] if args.competition else DOMESTIC):
        out=root/comp;out.mkdir(exist_ok=True)
        if (out/"selected_dynamic.json").exists():
            selected=json.loads((out/"selected_dynamic.json").read_text(encoding="utf-8"));hyper=DynamicHyper(**selected["hyperparameters"])
        else: hyper,selected=tune_dynamic(rows,comp,out)
        inner=records_for(train_rows(rows),comp,hyper,(2022,2023))
        promoted=estimate_promoted(rows,comp,hyper)
        markets=markets_for(inner,archive,out/"train_markets.json",args.workers)
        trust=calibrate_trust(inner,markets,selected["rho"])
        frozen={"engine_version":VERSION,"competition":comp,"selected":selected,"promoted":promoted,"trust":trust}
        dump(out/"frozen_train.json",frozen)
        frozen_hash=file_sha256(out/"frozen_train.json")
        # Only now construct Validation/Test records; they never reach tuning.
        reports={}
        for label,season in (("validation",2024),("test",2025)):
            rec=records_for(rows,comp,hyper,(season,),promoted)
            markets=markets_for(rec,archive,out/(label+"_markets.json"),args.workers)
            reports[label],details=evaluate(rec,markets,trust)
            dump(out/(label+"_paired.json"),details)
        reports["activation"]=gate(reports["validation"],reports["test"],selected,trust)
        reports["frozen_train_sha256"]=frozen_hash
        dump(out/"oos.json",reports)
        model=fit_dynamic(rows,comp,datetime(2026,6,1),hyper,promoted)
        dump(out/"runtime_model.json",model)
        print(comp,"COMPLETE",reports["activation"],flush=True)


if __name__=="__main__": main()
