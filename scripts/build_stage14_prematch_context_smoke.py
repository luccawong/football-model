"""Real Titan Stage14 pre-match-context smoke plus synthetic contract checks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gpt.prematch_context import build_prematch_context_updates
from gpt.quant_core import build_quant_packet
from gpt.stage14_auto import resolve_score_engine


def build(output: str, draws: int = 500) -> dict:
    source = json.loads((ROOT / "docs/data/stage14_production_smoke.json").read_text(encoding="utf-8"))
    cases = []
    for case in source["cases"]:
        quant = build_quant_packet(case["market_payload"])
        is_ucl = case["competition"] == "欧冠"
        args = dict(
            competition=case["competition"], season=case["season"],
            home_team=case["home_team"], away_team=case["away_team"],
            kickoff=case["kickoff"], quant_packet=quant,
            snapshot_phase=case.get("snapshot_phase"), mode="AUTO",
            prior_store=str(ROOT / "database/priors/model_1_titan_prior_store.json"),
            prior_packet=case.get("historical_prior_packet") if is_ucl else None,
            execution_path=case.get("formal_execution_path"), draws=draws,
        )
        before = resolve_score_engine(**args)
        context = build_prematch_context_updates(kickoff=case["kickoff"])
        after = resolve_score_engine(**args, context_updates=context)
        if after.get("score_engine_mode") == "HISTORICAL_BAYESIAN":
            audit = after.get("posterior", {}).get("context_audit", {})
            base_mu = audit.get("pre_context_mean_log_lambda", [None, None])
            final_mu = audit.get("post_context_mean_log_lambda", [None, None])
            import math
            base_lambda = [math.exp(x) if x is not None else None for x in base_mu]
            final_lambda = [math.exp(x) if x is not None else None for x in final_mu]
            delta = audit.get("context_delta_log_lambda", [0.0, 0.0])
        else:
            base_lambda = [before.get("lambda_home"), before.get("lambda_away")]
            final_lambda = [after.get("lambda_home"), after.get("lambda_away")]
            delta = after.get("context_delta_log_lambda", [0.0, 0.0])
        cases.append({
            "competition": case["competition"], "match_id": case["match_id"],
            "score_engine_mode": after.get("score_engine_mode"),
            "prior_used": after.get("prior_used"),
            "historical_prior_activation": after.get("historical_prior_activation"),
            "context_status": context["source_status"],
            "real_titan_calibration": context["real_titan_calibration"],
            "base_lambda_home": base_lambda[0], "base_lambda_away": base_lambda[1],
            "final_lambda_home": final_lambda[0], "final_lambda_away": final_lambda[1],
            "context_delta": delta,
            "raw_top10_unchanged_when_no_context": before.get("raw_top10") == after.get("raw_top10"),
            "top3_unchanged_when_no_context": before.get("top3") == after.get("top3"),
            "AH_gate": after.get("AH_gate_status"), "OU_gate": after.get("OU_references"),
        })

    synthetic = build_prematch_context_updates(
        recent_form={
            "validated": True, "effect_mode": "QUANTIFIED_OBSERVATION",
            "mean_log_lambda": [0.8, -0.1], "cov_log_lambda": [[0.1, 0], [0, 0.1]],
            "absorbed_fraction": 0.0, "evidence_timestamp": "2026-01-01T10:00:00Z",
            "calibration_ref": "synthetic-prematch-context-smoke", "calibration_status": "TEST_ONLY",
            "calibration_version": "smoke-v1", "provenance": {"source": "synthetic", "not_in_historical_prior": True},
        },
        kickoff="2026-01-01T15:00:00Z", context_snapshot_timestamp="2026-01-01T11:00:00Z",
        market_snapshot_timestamp="2026-01-01T12:00:00Z", historical_overlap_fraction=0.0,
        allow_test_calibration=True,
    )
    ucl = source["cases"][-1]
    synthetic_historical = resolve_score_engine(
        ucl["competition"], ucl["season"], ucl["home_team"], ucl["away_team"], ucl["kickoff"],
        build_quant_packet(ucl["market_payload"]), mode="HISTORICAL_BAYESIAN",
        prior_store=str(ROOT / "database/priors/model_1_titan_prior_store.json"),
        prior_packet=ucl.get("historical_prior_packet"), context_updates=synthetic,
        allow_test_calibration=True, execution_path=ucl.get("formal_execution_path"), draws=draws,
    )
    payload = {
        "status": "PASS" if all(row["raw_top10_unchanged_when_no_context"] and row["top3_unchanged_when_no_context"] for row in cases) and cases[-1]["score_engine_mode"] == "HISTORICAL_BAYESIAN" and cases[-1]["prior_used"] is True and cases[-1]["historical_prior_activation"] == "ACTIVE" else "FAIL",
        "draws": draws, "context_model_version": synthetic["context_model_version"],
        "real_titan_cases": cases,
        "synthetic_quantified_status": synthetic["source_status"]["RECENT_FORM"],
        "synthetic_quantified_no_future_leakage": synthetic["no_future_leakage"],
        "synthetic_historical_mode": synthetic_historical.get("score_engine_mode"),
        "synthetic_historical_overlap_effective_fraction": synthetic_historical.get("posterior", {}).get("context_updates", [{}])[0].get("effective_fraction") if synthetic_historical.get("posterior", {}).get("context_updates") else None,
    }
    path = ROOT / output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="validation/stage14_prematch_context_smoke.json")
    parser.add_argument("--draws", type=int, default=500)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.draws), ensure_ascii=False, indent=2))
