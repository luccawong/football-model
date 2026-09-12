from __future__ import annotations

import argparse
from datetime import timedelta
import json
from pathlib import Path

from gpt.prior_competition import (
    audit_competition_coverage,
    build_competition_store,
    competition_split,
    file_sha256,
    save_competition_store,
)
from gpt.prior_engine import (
    PriorEngineError,
    audit_titan_sqlite,
    calibrate_hyperparameters,
    load_titan_matches,
)


def _load_policy(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _is_boundary(value: float, candidates: list[float]) -> bool:
    return abs(value - min(candidates)) < 1e-12 or abs(value - max(candidates)) < 1e-12


def _coverage_map(coverage: dict) -> dict[str, dict]:
    return {str(x["competition"]): dict(x) for x in coverage["competition_coverage"]}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the raw Titan SQLite and calibrate MODEL_1 historical priors "
            "independently for every actual competition."
        )
    )
    parser.add_argument("--db", required=True, help="Path to football_odds_2021_2026.sqlite")
    parser.add_argument("--policy", default="config/model_1_prior_policy.json")
    parser.add_argument(
        "--output", default="database/priors/model_1_titan_prior_store.json",
        help="Candidate/final prior store. Formal activation remains SHADOW until OOS validation.",
    )
    parser.add_argument(
        "--report", default="validation/model_1_prior_calibration.json",
        help="Competition-level raw audit + train-only calibration report.",
    )
    parser.add_argument("--min-matches", type=int, default=None)
    args = parser.parse_args()

    policy = _load_policy(args.policy)
    min_matches = int(args.min_matches or policy.get("minimum_history", {}).get("completed_matches", 80))
    min_oos_seasons = int(policy.get("minimum_history", {}).get("oos_seasons", 4))

    raw_audit = audit_titan_sqlite(args.db)
    if raw_audit.get("status") != "VALID":
        print(json.dumps(raw_audit, ensure_ascii=False, indent=2))
        return 2
    rows, raw_audit = load_titan_matches(args.db)
    raw_audit = dict(raw_audit)
    raw_audit["dataset_sha256"] = file_sha256(args.db)

    coverage = audit_competition_coverage(
        args.db,
        min_completed_matches=min_matches,
        min_oos_seasons=min_oos_seasons,
    )
    coverage_by_comp = _coverage_map(coverage)
    competitions = list(coverage["competition_universe"])

    td = policy["time_decay"]
    hs = policy["hierarchical_shrinkage"]
    half_lives = [float(x) for x in td["research_candidate_half_life_days"]]
    team_sds = [float(x) for x in hs["research_candidate_team_sd"]]
    transition_sds = [float(x) for x in hs["research_candidate_transition_sd"]]

    split_by_competition: dict[str, dict] = {}
    calibration_by_competition: dict[str, dict] = {}
    selected: dict[str, dict[str, float]] = {}
    competition_status: dict[str, dict] = {}
    boundary_hits: list[dict] = []

    for competition in competitions:
        raw_cov = coverage_by_comp.get(competition, {})
        split = competition_split(
            rows,
            competition,
            min_oos_seasons=min_oos_seasons,
        )
        split_by_competition[competition] = split

        if raw_cov.get("prior_status") == "DATA_QUALITY_FAIL":
            competition_status[competition] = {
                "activation": "DISABLED",
                "reason": raw_cov.get("reason", "DATA_QUALITY_FAIL"),
                "raw_prior_status": raw_cov.get("prior_status"),
            }
            calibration_by_competition[competition] = {
                "status": "SKIPPED",
                "reason": raw_cov.get("reason", "DATA_QUALITY_FAIL"),
            }
            continue
        if raw_cov.get("prior_status") == "INSUFFICIENT_HISTORY":
            competition_status[competition] = {
                "activation": "INSUFFICIENT_HISTORY",
                "reason": raw_cov.get("reason", "TOO_FEW_COMPLETED_MATCHES"),
                "raw_prior_status": raw_cov.get("prior_status"),
            }
            calibration_by_competition[competition] = {
                "status": "CALIBRATION_REQUIRED",
                "reason": "INSUFFICIENT_HISTORY",
            }
            continue
        if split.get("status") != "VALID" or len(split.get("train", [])) < 2:
            competition_status[competition] = {
                "activation": "INSUFFICIENT_HISTORY",
                "reason": "INSUFFICIENT_OOS_HISTORY",
                "raw_prior_status": raw_cov.get("prior_status"),
            }
            calibration_by_competition[competition] = {
                "status": "CALIBRATION_REQUIRED",
                "reason": "INSUFFICIENT_OOS_HISTORY",
            }
            continue

        result = calibrate_hyperparameters(
            rows,
            league=competition,
            train_seasons=split["train"],
            half_life_candidates=half_lives,
            team_sd_candidates=team_sds,
            transition_sd_candidates=transition_sds,
            min_matches=min_matches,
        )
        calibration_by_competition[competition] = result
        if result.get("status") != "VALIDATED_ON_TRAIN_FOLDS":
            competition_status[competition] = {
                "activation": "SHADOW",
                "reason": result.get("reason", "TRAIN_CALIBRATION_FAILED"),
                "raw_prior_status": raw_cov.get("prior_status"),
            }
            continue

        chosen = dict(result["selected"])
        selected[competition] = chosen
        on_boundary = (
            _is_boundary(float(chosen["half_life_days"]), half_lives)
            or _is_boundary(float(chosen["team_sd"]), team_sds)
            or _is_boundary(float(chosen["transition_sd"]), transition_sds)
        )
        if on_boundary:
            boundary_hits.append({"competition": competition, **chosen})
            reason = "GRID_EXTENSION_REQUIRED"
        else:
            reason = "PENDING_OOS_ACTIVATION"
        competition_status[competition] = {
            "activation": "SHADOW",
            "reason": reason,
            "raw_prior_status": raw_cov.get("prior_status"),
            "selected_hyperparameters": chosen,
        }

    calibration_report = {
        "status": "TRAIN_CALIBRATION_COMPLETE_PENDING_OOS",
        "data_audit": raw_audit,
        "competition_universe": competitions,
        "competition_coverage": coverage["competition_coverage"],
        "competition_season_coverage": coverage["competition_season_coverage"],
        "split_by_competition": split_by_competition,
        "calibration_by_competition": calibration_by_competition,
        "selected_hyperparameters": selected,
        "competition_status_pre_oos": competition_status,
        "boundary_hits": boundary_hits,
        "anti_leakage": {
            "random_shuffle": False,
            "hyperparameters_see_validate": False,
            "hyperparameters_see_test": False,
            "market_data_in_prior": False,
            "global_cross_competition_baseline": False,
        },
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(calibration_report, ensure_ascii=False, indent=2), encoding="utf-8")

    # Build a candidate store for every successfully train-calibrated competition.
    # All such models stay SHADOW until validate_model_1_prior.py evaluates the
    # untouched test season and writes the final per-competition activation.
    if selected:
        max_date = max(r["match_date"] for r in rows)
        final_as_of = max_date + timedelta(seconds=1)
        store = build_competition_store(
            rows,
            hyperparameters_by_competition=selected,
            competition_status=competition_status,
            as_of=final_as_of,
            dataset_audit=raw_audit,
            calibration={
                "protocol": "COMPETITION_SPECIFIC_NESTED_SEASON_FORWARD_TRAIN_ONLY",
                "split_by_competition": split_by_competition,
                "selected_hyperparameters": selected,
                "calibration_report": str(report_path),
            },
            min_matches=min_matches,
        )
        save_competition_store(store, args.output)

    print(json.dumps({
        "status": calibration_report["status"],
        "output": args.output if selected else None,
        "report": str(report_path),
        "dataset_sha256": raw_audit["dataset_sha256"],
        "matches": raw_audit.get("matches_count"),
        "competitions": competitions,
        "calibrated_competitions": sorted(selected),
        "boundary_hits": boundary_hits,
        "activation": {k: v["activation"] for k, v in competition_status.items()},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
