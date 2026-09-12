from __future__ import annotations

import argparse
from datetime import timedelta
import json
from pathlib import Path
import sys

from gpt.prior_engine import (
    PriorEngineError,
    _season_start,
    audit_titan_sqlite,
    build_prior_store,
    calibrate_hyperparameters,
    load_titan_matches,
    save_prior_store,
)


def _load_policy(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _split_seasons(rows: list[dict]) -> dict[str, list[str]]:
    by_start: dict[int, str] = {}
    for row in rows:
        by_start.setdefault(int(row["season_start"]), str(row["season"]))
    ordered = [by_start[k] for k in sorted(by_start)]
    if len(ordered) < 5:
        raise PriorEngineError(
            f"At least five seasons are required for the default train/validate/test protocol; got {ordered}."
        )
    return {
        "train": ordered[:-2],
        "validate": [ordered[-2]],
        "test": [ordered[-1]],
    }


def _is_boundary(value: float, candidates: list[float]) -> bool:
    return abs(value - min(candidates)) < 1e-12 or abs(value - max(candidates)) < 1e-12


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Titan SQLite, select leak-safe prior hyperparameters, and build MODEL_1 prior store."
    )
    parser.add_argument("--db", required=True, help="Path to football_odds_2021_2026.sqlite")
    parser.add_argument(
        "--policy", default="config/model_1_prior_policy.json",
        help="Prior policy JSON. Candidate grids are research grids, not fixed conclusions.",
    )
    parser.add_argument(
        "--output", default="database/priors/model_1_titan_prior_store.json",
        help="Generated prior store. Do not commit the raw SQLite database.",
    )
    parser.add_argument(
        "--report", default="validation/model_1_prior_calibration.json",
        help="Calibration audit report.",
    )
    parser.add_argument("--min-matches", type=int, default=80)
    args = parser.parse_args()

    policy = _load_policy(args.policy)
    audit = audit_titan_sqlite(args.db)
    if audit.get("status") != "VALID":
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        return 2

    rows, audit = load_titan_matches(args.db)
    split = _split_seasons(rows)
    leagues = sorted({r["league"] for r in rows})
    td = policy["time_decay"]
    hs = policy["hierarchical_shrinkage"]
    half_lives = [float(x) for x in td["research_candidate_half_life_days"]]
    team_sds = [float(x) for x in hs["research_candidate_team_sd"]]
    transition_sds = [float(x) for x in hs["research_candidate_transition_sd"]]

    calibration_by_league: dict[str, dict] = {}
    selected: dict[str, dict[str, float]] = {}
    boundary_hits: list[dict] = []
    for league in leagues:
        result = calibrate_hyperparameters(
            rows,
            league=league,
            train_seasons=split["train"],
            half_life_candidates=half_lives,
            team_sd_candidates=team_sds,
            transition_sd_candidates=transition_sds,
            min_matches=args.min_matches,
        )
        calibration_by_league[league] = result
        if result.get("status") != "VALIDATED_ON_TRAIN_FOLDS":
            continue
        chosen = dict(result["selected"])
        selected[league] = chosen
        if (
            _is_boundary(float(chosen["half_life_days"]), half_lives)
            or _is_boundary(float(chosen["team_sd"]), team_sds)
            or _is_boundary(float(chosen["transition_sd"]), transition_sds)
        ):
            boundary_hits.append({"league": league, **chosen})

    report = {
        "status": "GRID_EXTENSION_REQUIRED" if boundary_hits else "CALIBRATED_TRAIN_ONLY",
        "data_audit": audit,
        "split": split,
        "leagues": leagues,
        "calibration_by_league": calibration_by_league,
        "selected_hyperparameters": selected,
        "boundary_hits": boundary_hits,
        "anti_leakage": {
            "random_shuffle": False,
            "hyperparameters_see_validate": False,
            "hyperparameters_see_test": False,
            "market_data_in_prior": False,
        },
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if boundary_hits:
        print(
            "One or more hyperparameter winners are on a research-grid boundary. "
            "Extend the grid before freezing production parameters.",
            file=sys.stderr,
        )
        print(json.dumps(boundary_hits, ensure_ascii=False, indent=2), file=sys.stderr)
        return 3
    if set(selected) != set(leagues):
        missing = sorted(set(leagues) - set(selected))
        print(f"Calibration unavailable for leagues: {missing}", file=sys.stderr)
        return 4

    # Production store is fitted only after hyperparameters have been frozen from
    # inner train folds.  It may use the complete historical archive after the
    # validation/test report has been frozen; this does not retune hyperparameters.
    max_date = max(r["match_date"] for r in rows)
    final_as_of = max_date + timedelta(seconds=1)
    store = build_prior_store(
        rows,
        hyperparameters_by_league=selected,
        as_of=final_as_of,
        dataset_audit=audit,
        calibration={
            "protocol": "NESTED_SEASON_FORWARD_TRAIN_ONLY",
            "split": split,
            "selected_hyperparameters": selected,
            "calibration_report": str(report_path),
        },
        min_matches=args.min_matches,
    )
    save_prior_store(store, args.output)
    print(
        json.dumps(
            {
                "status": "OK",
                "output": args.output,
                "calibration_ref": store["calibration_ref"],
                "split": split,
                "matches": audit.get("usable_completed_matches"),
                "leagues": leagues,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
