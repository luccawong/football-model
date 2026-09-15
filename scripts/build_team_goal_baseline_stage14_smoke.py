"""Audit-only Stage14 smoke: prove team-goal context does not change Top3."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gpt.quant_core import build_quant_packet
from gpt.stage14_auto import resolve_score_engine


def build(database: str, output: str, draws: int = 500) -> dict:
    root = ROOT
    source = json.loads((root / "docs/data/stage14_production_smoke.json").read_text(encoding="utf-8"))
    rows = []
    for case in source["cases"][:5]:
        quant = build_quant_packet(case["market_payload"])
        args = dict(
            competition=case["competition"], season=case["season"],
            home_team=case["home_team"], away_team=case["away_team"],
            kickoff=case["kickoff"], quant_packet=quant,
            snapshot_phase=case.get("snapshot_phase"), mode="MARKET_ONLY_FORMAL",
            execution_path=case["formal_execution_path"], draws=draws,
        )
        before = resolve_score_engine(**args)
        after = resolve_score_engine(**args, team_goal_baseline_database=database)
        before_top3 = [r["score"] for r in before.get("top3", [])]
        after_top3 = [r["score"] for r in after.get("top3", [])]
        raw_top10_unchanged = before.get("raw_top10") == after.get("raw_top10")
        lambda_unchanged = (before.get("lambda_home"), before.get("lambda_away")) == (after.get("lambda_home"), after.get("lambda_away"))
        ah_unchanged = before.get("AH_gate_status") == after.get("AH_gate_status")
        ou_unchanged = before.get("OU_references") == after.get("OU_references")
        audit = after.get("team_goal_baseline_audit", {})
        rows.append({
            "competition": case["competition"], "match_id": case["match_id"],
            "history_lambda_home": audit.get("history_lambda_home"),
            "history_lambda_away": audit.get("history_lambda_away"),
            "market_lambda_home": audit.get("market_lambda_home"),
            "market_lambda_away": audit.get("market_lambda_away"),
            "market_home_lambda_residual": audit.get("market_home_lambda_residual"),
            "market_away_lambda_residual": audit.get("market_away_lambda_residual"),
            "market_total_residual": audit.get("market_total_residual"),
            "market_goal_residual": audit.get("market_goal_residual"),
            "standardized_residuals": audit.get("standardized_residuals"),
            "deviation_labels": audit.get("deviation_labels"),
            "baseline_status": audit.get("status"),
            "stage14_top3_before": before_top3, "stage14_top3_after": after_top3,
            "stage14_top3_unchanged": before_top3 == after_top3,
            "stage14_raw_top10_unchanged": raw_top10_unchanged,
            "stage14_lambda_unchanged": lambda_unchanged,
            "stage14_ah_gate_unchanged": ah_unchanged,
            "stage14_ou_unchanged": ou_unchanged,
            "formal_model_1_weight_impact": audit.get("formal_model_1_weight_impact"),
        })
    payload = {"status": "PASS" if all(r["stage14_top3_unchanged"] and r["stage14_raw_top10_unchanged"] and r["stage14_lambda_unchanged"] and r["stage14_ah_gate_unchanged"] and r["stage14_ou_unchanged"] for r in rows) else "FAIL",
               "draws": draws, "research_only": True, "cases": rows}
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default="database/research/team_goal_baselines.sqlite")
    parser.add_argument("--output", default="validation/team_goal_baseline_stage14_smoke.json")
    parser.add_argument("--draws", type=int, default=500)
    args = parser.parse_args()
    print(json.dumps(build(args.database, args.output, args.draws), ensure_ascii=False, indent=2))
