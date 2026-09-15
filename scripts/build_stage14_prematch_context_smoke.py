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
        args = dict(
            competition=case["competition"], season=case["season"],
            home_team=case["home_team"], away_team=case["away_team"],
            kickoff=case["kickoff"], quant_packet=quant,
            snapshot_phase=case.get("snapshot_phase"), mode="MARKET_ONLY_FORMAL",
            execution_path=case.get("formal_execution_path"), draws=draws,
        )
        before = resolve_score_engine(**args)
        context = build_prematch_context_updates(kickoff=case["kickoff"])
        after = resolve_score_engine(**args, context_updates=context)
        cases.append({
            "competition": case["competition"], "match_id": case["match_id"],
            "context_status": context["source_status"],
            "real_titan_calibration": context["real_titan_calibration"],
            "raw_top10_unchanged": before.get("raw_top10") == after.get("raw_top10"),
            "top3_unchanged": before.get("top3") == after.get("top3"),
            "lambda_unchanged": [before.get("lambda_home"), before.get("lambda_away")] == [after.get("lambda_home"), after.get("lambda_away")],
            "ah_gate_unchanged": before.get("AH_gate_status") == after.get("AH_gate_status"),
            "ou_unchanged": before.get("OU_references") == after.get("OU_references"),
        })

    synthetic = build_prematch_context_updates(
        recent_form={
            "validated": True, "effect_mode": "QUANTIFIED_OBSERVATION",
            "mean_log_lambda": [0.8, -0.1], "cov_log_lambda": [[0.1, 0], [0, 0.1]],
            "absorbed_fraction": 0.0, "evidence_timestamp": "2026-01-01T10:00:00Z",
            "calibration_ref": "synthetic-prematch-context-smoke",
        },
        kickoff="2026-01-01T15:00:00Z", market_snapshot_timestamp="2026-01-01T12:00:00Z",
    )
    payload = {
        "status": "PASS" if all(all(x for x in row.values() if isinstance(x, bool)) for row in cases) else "FAIL",
        "draws": draws, "context_model_version": synthetic["context_model_version"],
        "real_titan_cases": cases,
        "synthetic_quantified_status": synthetic["source_status"]["RECENT_FORM"],
        "synthetic_quantified_no_future_leakage": synthetic["no_future_leakage"],
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
