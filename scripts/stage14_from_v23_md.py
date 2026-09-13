from __future__ import annotations

import argparse
import json
from pathlib import Path

from gpt.quant_core import build_quant_packet
from gpt.stage14_auto import market_reconstruction_top3, resolve_score_engine
from src.parser.titan_md import read_markdown_tables


CORE = ("Pinnacle", "Bet365", "Macau")


def parse_line(value):
    text = str(value).strip()
    if "/" in text:
        parts = [float(x) for x in text.split("/")]
        return sum(parts) / len(parts)
    return float(text)


def build_payload(tables, match_id):
    companies = {}
    euro = [r for r in tables.get("Europe_1x2", []) if str(r.get("match_id")) == str(match_id)]
    ou = [r for r in tables.get("OverUnder_Current", []) if str(r.get("match_id")) == str(match_id)]

    for row in euro:
        name = row.get("company")
        if not name:
            continue
        prices = [row.get("current_home"), row.get("current_draw"), row.get("current_away")]
        if all(v is not None for v in prices):
            companies.setdefault(name, {})["one_x_two"] = [float(v) for v in prices]

    for row in ou:
        name = row.get("company")
        if not name or row.get("current_line") is None:
            continue
        if row.get("current_left") is None or row.get("current_right") is None:
            continue
        companies.setdefault(name, {})["ou"] = {
            "line": parse_line(row["current_line"]),
            "over": 1.0 + float(row["current_left"]),
            "under": 1.0 + float(row["current_right"]),
            "role": "dynamic" if name in CORE else "reference",
        }

    usable = {name: data for name, data in companies.items() if "one_x_two" in data and "ou" in data}
    return {"match_id": str(match_id), "companies": usable}


def _load_json(value):
    if value is None:
        return None
    path = Path(value)
    return json.loads(path.read_text(encoding="utf-8"))


def _formal_execution_path(execution_path):
    path = dict(execution_path or {})
    ou = path.get("ou")
    if not isinstance(ou, dict):
        raise ValueError(
            "OU_DIRECTION_REQUIRED: formal MODEL_1 Top3 requires execution_path.ou "
            "with side=OVER|UNDER and line; OU ticket may still be NO."
        )
    side = str(ou.get("side", "")).upper()
    if side not in {"OVER", "UNDER"} or ou.get("line") is None:
        raise ValueError(
            "OU_DIRECTION_REQUIRED: execution_path.ou must contain side=OVER|UNDER and line."
        )
    ou = dict(ou)
    ou["side"] = side
    ou["line"] = float(ou["line"])
    ou["hard_gate"] = True
    path["ou"] = ou
    return path


def _enforce_ou_top3(score):
    out = dict(score)
    top3 = [dict(row) for row in out.get("top3", []) if bool(row.get("ou_ok", False))]
    out["top3"] = top3
    if "execution_filtered_top3" in out:
        out["execution_filtered_top3"] = top3
    if any(key in out for key in ("Top1", "Top2", "Top3")):
        out["Top1"] = top3[0] if len(top3) > 0 else None
        out["Top2"] = top3[1] if len(top3) > 1 else None
        out["Top3"] = top3[2] if len(top3) > 2 else None
    out["OU_gate_status"] = "APPLIED_HARD_DIRECTION_ONLY"
    if not top3 and out.get("status") in {"FORMAL_SCORE_TOP3", "BAYESIAN_POSTERIOR_TOP3"}:
        out["status"] = "SCORELINE_CONFLICT"
        out["reason"] = "NO_SCORELINE_SATISFIES_HARD_WINNER_AH_OU_GATES"
    return out


def build_stage14(
    path,
    match_id,
    *,
    prior_packet=None,
    prior_store=None,
    prior_context=None,
    context_updates=None,
    execution_path=None,
    mode="AUTO",
    snapshot_phase=None,
):
    tables = read_markdown_tables(path)
    quant = build_quant_packet(build_payload(tables, match_id))
    context = dict(prior_context or {})
    formal_execution = _formal_execution_path(execution_path)
    score = resolve_score_engine(
        str(context.get("competition") or context.get("league") or "UNKNOWN"),
        str(context.get("season") or "UNKNOWN"),
        str(context.get("home_team") or "UNKNOWN"),
        str(context.get("away_team") or "UNKNOWN"),
        str(context.get("kickoff") or context.get("match_date") or quant.get("snapshot_time") or "UNKNOWN"),
        quant,
        snapshot_phase=snapshot_phase,
        mode=mode,
        prior_packet=prior_packet,
        prior_store=prior_store,
        context_updates=context_updates,
        execution_path=formal_execution,
    )
    score = _enforce_ou_top3(score)
    research = {}
    for company in CORE:
        if company in quant.get("reconstruction", {}):
            research[company] = market_reconstruction_top3(quant, company)
    return {
        "match_id": str(match_id),
        "formal_model": "MODEL_1",
        "formal_stage14": score,
        "research_market_reconstruction": research,
        "quant_engine_version": quant.get("engine_version"),
        "production_default_mode": "AUTO",
        "formal_correlated_market_model_enabled": True,
        "formal_ou_direction_required": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown")
    parser.add_argument("match_id")
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--prior-json", help="Pre-built validated prior packet JSON")
    source.add_argument("--prior-store", help="Calibrated Titan historical prior store JSON")
    parser.add_argument(
        "--prior-context-json",
        help="Required with --prior-store unless the caller injects match context elsewhere; must contain league/season/home_team/away_team.",
    )
    parser.add_argument("--context-json")
    parser.add_argument("--execution-json")
    parser.add_argument("--mode", choices=("AUTO", "HISTORICAL_BAYESIAN", "MARKET_ONLY_FORMAL"), default="AUTO")
    parser.add_argument("--snapshot-phase", choices=("opening", "closing", "current"))
    args = parser.parse_args()

    prior = _load_json(args.prior_json)
    store = args.prior_store
    prior_context = _load_json(args.prior_context_json)
    if store is not None and prior_context is None and args.mode == "HISTORICAL_BAYESIAN":
        parser.error("Explicit historical mode with --prior-store requires --prior-context-json.")
    context = _load_json(args.context_json)
    execution = _load_json(args.execution_json)
    print(
        json.dumps(
            build_stage14(
                args.markdown,
                args.match_id,
                prior_packet=prior,
                prior_store=store,
                prior_context=prior_context,
                context_updates=context,
                execution_path=execution,
                mode=args.mode,
                snapshot_phase=args.snapshot_phase,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
