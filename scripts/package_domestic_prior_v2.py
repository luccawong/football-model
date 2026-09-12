"""Audit completed V2 outputs and package only derived state/evidence, no raw DB."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path
import shutil

import numpy as np

from gpt.domestic_prior import DOMESTIC, VERSION, pd
from gpt.domestic_gate import activation_gate
from gpt.prior_competition import file_sha256
from gpt.stage14_bayesian import _normal_update
from scripts.validate_domestic_prior_v2 import RAW_SHA, dump, evaluate, predictive

SLUGS=dict(zip(DOMESTIC,("epl","laliga","seriea","bundesliga","ligue1")))


def load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def fmt(x): return "—" if x is None else f"{x:.6f}"
def ci(p): return "["+", ".join(f"{x:+.6f}" for x in p["bootstrap95"])+"]"


def package(root,repo):
    provenance=load(root/"provenance.json")
    if provenance["sha256"]!=RAW_SHA or provenance["raw_count"]!=13090:
        raise ValueError("Invalid mother source provenance")
    artifacts=repo/"docs/data/domestic_prior_v2";artifacts.mkdir(parents=True,exist_ok=True)
    store_path=repo/"database/priors/model_1_titan_prior_store.json";store=load(store_path)
    store.setdefault("domestic_v2",{})
    results={};audit={};summary=[]
    lines=["## Domestic Prior V2", "", "This section supersedes the domestic V1 results above; the three European models and their gates remain frozen.", "",
           "### Protocol and provenance", "",
           f"- Mother SQLite SHA256: `{RAW_SHA}`; **13,090 raw matches**. Only five domestic competitions were refitted.",
           "- Train: 2021-22 through 2023-24. Inner season-forward evaluation: 2022-23 and 2023-24. Validation: 2024-25; Test: 2025-26. No random split.",
           "- The selected structure, half-life, team SD, transition SD, rho, process covariance and phase-specific kappa were frozen and hashed before constructing outer OOS records. No selection was revised after observing Test.",
           "- Search compares monthly Laplace random-walk filtering and rolling 30/60/90-day refits. All candidates refresh at month start using strictly earlier results. Rolling windows use the previous-season posterior as their anchor, not the overlapping previous rolling window.",
           "- Attack/defence are jointly opponent-adjusted. Competition baseline/HFA, full Laplace parameter covariance, previous-season transitions, and hierarchical shrinkage are retained. A new team uses the Train-estimated domestic entrant class when six historical entrant team-seasons exist; otherwise competition mean plus current-season evidence.",
           "- Train selection minimizes conditional Dixon–Coles correct-score predictive NLL; Top3, 1X2 Brier and RPS are recorded for each candidate and constrained at release. The search uses two deterministic coordinate passes per structure, not an exhaustive global optimum claim.",
           "- Rho is fitted on first Train inner-OOS scores, its shrinkage factor is selected by the second Train season, then its estimate is refit on pooled Train inner-OOS records. A selected zero is evidence-driven shrinkage, not hard-coded rho=0. Rho bounds [-0.16, 0.027] guarantee positive DC cells over the existing runtime lambda support [0.05, 6].",
           "- Process covariance is the positive-semidefinite projection of Train inner-OOS log-rate residual second moments after subtracting Poisson and Laplace uncertainty. Effective prior covariance is `kappa * (Laplace + process)`; symmetric/PD checks apply. Kappa is fitted separately for opening and closing with full lognormal predictive NLL; it never modifies the prior mean.",
           "- A uses the existing correlated Pinnacle/Bet365/Macau market reconstruction. C uses its Bayesian normal update with the historical prior. B uses historical Laplace + process uncertainty without phase-specific market trust scaling, so B is identical on equal opening/closing samples.",
           "- Full lognormal integration uses deterministic 12×12 Gauss–Hermite nodes and the existing [0.05, 6] lambda support. A 24×24 C audit is included below; runtime retains its existing Monte Carlo predictive integrator. No manual prior/market weights are introduced.",
           "- Opening 1X2/OU and closing 1X2/OU are loaded independently. AH evaluation uses the corresponding archived phase-specific core-book line and five-outcome settlement-equivalent calibration. Opening/closing archives are not synchronized timestamped intraday observations; no intraday decay policy is claimed.",
           "- Gate uses the intersection of the old policy/report: C NLL <= A in **both** Validation/Test; Top3 harm <= 1 pp; no 1X2 Brier or RPS deterioration; OU/AH Brier harm <= 0.005; at least 80 common samples per period; no unresolved Train boundary. SHADOW blocks formal Stage14, including explicit SHADOW packets. Raw posterior mass and existing AH execution hard gate are unchanged.",
           "- All Train grid boundaries stay visible. They were not extended or retuned after Test. No league is activated simply because its point estimate improves in one period.","",
           "### Test comparison", "",
           "| Competition | Open A NLL | Open C NLL | Close A NLL | Close C NLL | Top3 open A/C | Top3 close A/C | ΔNLL open/close | bootstrap CI open / close | activation |",
           "|---|---:|---:|---:|---:|---|---|---|---|---|"]
    for comp in DOMESTIC:
        folder=root/comp;frozen=load(folder/"frozen_train.json");oos=load(folder/"oos.json")
        if file_sha256(folder/"frozen_train.json")!=oos["frozen_train_sha256"]:
            raise ValueError("Frozen Train changed after OOS: "+comp)
        expected=activation_gate(oos["validation"],oos["test"],frozen["selected"],frozen["trust"])
        if expected["activation"]!=oos["activation"]["activation"] or any(expected[p]["status"]!=oos["activation"][p]["status"] for p in ("opening","closing")):
            raise ValueError("Release gate mismatch: "+comp)
        model=load(folder/"runtime_model.json")
        payload={"competition":comp,"frozen":frozen,"oos":oos,"model":model}
        model_path=repo/"database/priors/domestic_v2"/(SLUGS[comp]+".json")
        dump(model_path,payload)
        store["domestic_v2"][comp]={"path":model_path.relative_to(store_path.parent).as_posix(),"sha256":file_sha256(model_path)}
        store["competition_status"][comp]={"activation":expected["activation"],"reason":"DOMESTIC_V2_OOS_GATE",
                                           "opening":expected["opening"],"closing":expected["closing"],"lifecycle":expected["lifecycle"]}
        slug=SLUGS[comp];shutil.copyfile(folder/"frozen_train.json",artifacts/(slug+"_frozen_train.json"))
        dump(artifacts/(slug+"_oos.json"),oos)
        dump(artifacts/(slug+"_search.json"),load(folder/"search.json"))
        comp_audit={};paired_rows=[]
        for period in ("validation","test"):
            details=load(folder/(period+"_paired.json"));markets=load(folder/(period+"_markets.json"))
            records=list({r["match_id"]:{k:v for k,v in r.items() if k not in ("phase","score_nll")} for r in details}.values())
            rebuilt,_=evaluate(records,markets,frozen["trust"])
            errors=[]
            for phase in ("opening","closing"):
                for name in ("A","B","C"):
                    for metric in ("correct_score_NLL","Top3_coverage","Top1_exact_score_hit_rate","1X2_Brier","RPS","OU_over2_5_Brier","AH_settlement_aware_Brier"):
                        errors.append(abs(rebuilt[phase][name][metric]-oos[period][phase][name][metric]))
            if max(errors)>1e-10: raise ValueError("Metric replay mismatch: "+comp+period)
            quadrature=[]
            for r in details:
                phase=r["phase"];params=frozen["trust"][phase];market=markets[r["match_id"]+"|"+phase]
                m=market["market"]
                mu,cov=_normal_update(np.array(r["mean"]),pd(params["kappa"]*(np.array(r["cov"])+params["process_covariance"])),
                                     np.array(m["mean_log_lambda"]),np.array(m["cov_log_lambda"]))
                g=predictive(mu,cov,params["rho"],order=24)
                delta=-np.log(g[tuple(r["y"])])-r["score_nll"]["C"]
                quadrature.append(float(delta))
                paired_rows.append({**r,"period":period,"market_likelihood":m,"ah_home_handicap":market["ah"]})
            comp_audit[period]={"max_metric_replay_error":max(errors),"C_quadrature_24_minus_12_mean_NLL":float(np.mean(quadrature)),
                                 "C_quadrature_24_minus_12_max_abs_NLL":float(np.max(np.abs(quadrature))),"paired_phase_rows":len(details)}
        raw=json.dumps(paired_rows,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode("utf-8")
        (artifacts/(slug+"_paired.json.gz")).write_bytes(gzip.compress(raw,mtime=0))
        audit[comp]=comp_audit;results[comp]=(frozen,oos)
        o,c=oos["test"]["opening"],oos["test"]["closing"]
        po,pc=o["paired_C_minus_A"],c["paired_C_minus_A"]
        lines.append(f"| {comp} | {fmt(o['A']['correct_score_NLL'])} | {fmt(o['C']['correct_score_NLL'])} | {fmt(c['A']['correct_score_NLL'])} | {fmt(c['C']['correct_score_NLL'])} | {o['A']['Top3_coverage']:.3%}/{o['C']['Top3_coverage']:.3%} | {c['A']['Top3_coverage']:.3%}/{c['C']['Top3_coverage']:.3%} | {po['mean_delta']:+.6f}/{pc['mean_delta']:+.6f} | {ci(po)} / {ci(pc)} | {expected['activation']} |")
        for phase in ("opening","closing"):
            p=oos["test"][phase];d=p["paired_C_minus_A"]
            summary.append({"competition":comp,"phase":phase,"n":p["C"]["n"],"A_NLL":p["A"]["correct_score_NLL"],"C_NLL":p["C"]["correct_score_NLL"],
                            "A_Top3":p["A"]["Top3_coverage"],"C_Top3":p["C"]["Top3_coverage"],"delta":d["mean_delta"],"CI_low":d["bootstrap95"][0],"CI_high":d["bootstrap95"][1],"activation":expected[phase]["status"]})
    for comp,(frozen,oos) in results.items():
        h=frozen["selected"]["hyperparameters"];rho=frozen["selected"]["rho"]
        lines += ["",f"### {comp}","",f"- Selected state: **{h['structure']}**; half-life **{h['half_life_days']:g} days**; team SD **{h['team_sd']:g}**; transition SD **{h['transition_sd']:g}**.",
                  f"- Historical rho **{rho:.8f}**; Train forward shrinkage **{frozen['selected']['rho_shrinkage']:g}**; searched **{frozen['selected']['candidate_count']}** candidate settings; unresolved boundaries: `{frozen['selected']['boundary']}`.",
                  f"- Process covariance: `{json.dumps(frozen['trust']['opening']['process_covariance'])}`.",
                  f"- Kappa opening **{frozen['trust']['opening']['kappa']:.6f}**, closing **{frozen['trust']['closing']['kappa']:.6f}**; trust boundaries opening/closing: `{frozen['trust']['opening']['boundary']}/{frozen['trust']['closing']['boundary']}`.",
                  f"- Promoted/new entrant class: `{json.dumps(frozen['promoted'],ensure_ascii=False)}`.",
                  f"- Frozen Train SHA256: `{oos['frozen_train_sha256']}`.",
                  "", "| Period | Phase | Model | N | Score NLL | Top1 | Top3 | 1X2 Brier | RPS | OU Brier | OU logloss | OU ECE | AH Brier | AH ECE |",
                  "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for period in ("validation","test"):
            for phase in ("opening","closing"):
                for name in ("A","B","C"):
                    m=oos[period][phase][name]
                    vals=[m[k] for k in ("correct_score_NLL","Top1_exact_score_hit_rate","Top3_coverage","1X2_Brier","RPS","OU_over2_5_Brier","OU_over2_5_logloss")]
                    vals += [m["OU_over2_5_calibration"]["ece"],m["AH_settlement_aware_Brier"],m["AH_cover_equivalent_calibration"]["ece"]]
                    lines.append(f"| {period} | {phase} | {name} | {m['n']} | "+" | ".join(fmt(v) for v in vals)+" |")
        lines += ["", "| Period | Phase | Mean C−A NLL | Median C−A NLL | Paired bootstrap 95% CI | C higher actual-score probability |", "|---|---|---:|---:|---|---:|"]
        for period in ("validation","test"):
            for phase in ("opening","closing"):
                d=oos[period][phase]["paired_C_minus_A"]
                lines.append(f"| {period} | {phase} | {d['mean_delta']:+.6f} | {d['median_delta']:+.6f} | {ci(d)} | {d['fraction_C_higher_actual_score_probability']:.3%} |")
        for phase in ("opening","closing"):
            lines += ["",f"- **{phase} status: {oos['activation'][phase]['status']}**. Reasons: "+", ".join(oos["activation"][phase]["reasons"])+"."]
        lines += [f"- **Final activation: {oos['activation']['activation']}**."]
    lines += ["", "### Numerical replay audit", "", "| Competition | Period | Metric replay max error | 24-node minus 12-node mean C NLL | Max absolute per-match C NLL error |", "|---|---|---:|---:|---:|"]
    for comp,periods in audit.items():
        for period,a in periods.items():
            lines.append(f"| {comp} | {period} | {a['max_metric_replay_error']:.3g} | {a['C_quadrature_24_minus_12_mean_NLL']:.3g} | {a['C_quadrature_24_minus_12_max_abs_NLL']:.3g} |")
    lines += ["", "### Evidence and limitations", "",
              "- `docs/data/domestic_prior_v2/` contains every Train search result, the frozen Train certificates, full OOS metrics/calibration bins, and compressed match-level predictions with both market phases. The paired bootstrap uses 5,000 match resamples with seed 20260912. Intervals are not adjusted for within-week/team dependence or multiple comparisons.",
              "- OOS Top1/Top3 measure the raw predictive distribution. Archived fixtures have no formal MODEL_1 execution ticket, so execution Top3 is not fabricated from a bookmaker handicap. The existing AH hard-gate tests still apply to formal runtime.",
              "- Rho, process uncertainty and kappa are estimated from the limited two Train inner-OOS seasons. Train search is finite; boundary winners stay SHADOW and are not evidence of a resolved optimum.",
              "- The production resolver requires kickoff, rejects a model containing future results, verifies the packaged model hash, and rechecks phase-specific OOS evidence before ACTIVE. `DomesticPriorResolver(store).resolve_prior(competition, season, home_team, away_team, kickoff)` defaults to the conservative closing phase; explicit `snapshot_phase='opening'` is supported. There is no inferred early/late time decay or market-prior fallback.",
              "- The packaged state includes completed results through May 2026. New results require a new historical-state build with the frozen Train parameters; this package does not scrape live results.",
              "- **All five domestic competitions remain SHADOW.** Test observations above are evaluation evidence only and must not be recycled into parameter tuning. European ACTIVE/SHADOW states and packed numerical data are unchanged.", ""]
    report_path=repo/"docs/MODEL_1_TITAN_PRIOR_VALIDATION_20260912.md"
    old=report_path.read_text(encoding="utf-8").split("\n## Domestic Prior V2",1)[0].rstrip()
    report_path.write_text(old+"\n\n"+"\n".join(lines),encoding="utf-8")
    dump(store_path,store);dump(artifacts/"audit.json",audit)
    with (artifacts/"test_summary.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    manifest=load(repo/"database/priors/model_1_titan_prior_manifest.json")
    manifest["domestic_v2"]={"engine_version":VERSION,"report":"docs/MODEL_1_TITAN_PRIOR_VALIDATION_20260912.md",
                             "competitions":list(DOMESTIC),"all_runs_complete":True,"activation":{c:results[c][1]["activation"] for c in DOMESTIC}}
    dump(repo/"database/priors/model_1_titan_prior_manifest.json",manifest)
    print(json.dumps(audit,ensure_ascii=False,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--repo",default=".")
    a=p.parse_args();package(Path(a.root),Path(a.repo))
