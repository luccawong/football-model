from __future__ import annotations

from datetime import datetime
import sqlite3

import numpy as np
import pytest

from gpt.prior_engine import (
    HyperParameters,
    PriorEngineError,
    audit_titan_sqlite,
    build_prior_packet,
    build_prior_packet_from_model,
    calibrate_hyperparameters,
    fit_league_model,
)
from gpt.stage14_auto import automatic_top3


def _rows():
    teams = ["A", "B", "C", "D"]
    seasons = [("2021-22", 2021), ("2022-23", 2022), ("2023-24", 2023)]
    rows = []
    match_id = 1
    for season, start in seasons:
        for cycle in range(4):
            for i, home in enumerate(teams):
                away = teams[(i + cycle + 1) % len(teams)]
                if home == away:
                    continue
                strength_h = {"A": 2, "B": 1, "C": 0, "D": -1}[home]
                strength_a = {"A": 2, "B": 1, "C": 0, "D": -1}[away]
                hg = max(0, 1 + int(strength_h > strength_a) + (cycle % 2))
                ag = max(0, int(strength_a >= strength_h))
                rows.append(
                    {
                        "match_id": str(match_id),
                        "match_date": datetime(start, 8 + min(cycle, 3), 1 + i),
                        "league": "德甲",
                        "season": season,
                        "season_start": start,
                        "home_team": home,
                        "away_team": away,
                        "home_score": hg,
                        "away_score": ag,
                    }
                )
                match_id += 1
    rows.sort(key=lambda r: r["match_date"])
    return rows


def _quant_packet():
    return {
        "engine_version": "q",
        "match_id": "future-1",
        "snapshot_time": "2024-08-20T10:00:00Z",
        "reconstruction": {
            "Pinnacle": {"lambda_home": 1.8, "lambda_away": 1.05, "rho": -0.05, "max_abs_residual": 0.004},
            "Bet365": {"lambda_home": 1.75, "lambda_away": 1.10, "rho": -0.04, "max_abs_residual": 0.006},
            "Macau": {"lambda_home": 1.85, "lambda_away": 1.00, "rho": -0.06, "max_abs_residual": 0.005},
        },
    }


def test_sqlite_audit_requires_real_minimum_fields(tmp_path):
    path = tmp_path / "titan.sqlite"
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE matches (match_id TEXT, kickoff TEXT, competition TEXT, season TEXT, "
        "home_team TEXT, away_team TEXT, home_score INTEGER, away_score INTEGER)"
    )
    con.execute(
        "INSERT INTO matches VALUES ('1','2024-01-01 12:00:00','德甲','2023-24','A','B',2,1)"
    )
    con.commit()
    con.close()
    audit = audit_titan_sqlite(path)
    assert audit["status"] == "VALID"
    assert audit["matches_count"] == 1
    assert audit["field_mapping"]["match_date"] == "kickoff"
    assert audit["field_mapping"]["league"] == "competition"

    bad = tmp_path / "bad.sqlite"
    con = sqlite3.connect(bad)
    con.execute(
        "CREATE TABLE matches (match_id TEXT, kickoff TEXT, competition TEXT, "
        "home_team TEXT, away_team TEXT, home_score INTEGER, away_score INTEGER)"
    )
    con.commit()
    con.close()
    audit_bad = audit_titan_sqlite(bad)
    assert audit_bad["status"] == "INVALID"
    assert "season" in audit_bad["missing_required_fields"]


def test_hierarchical_prior_produces_estimated_positive_definite_covariance():
    rows = _rows()
    model = fit_league_model(
        rows,
        league="德甲",
        as_of="2024-08-01",
        hyperparameters=HyperParameters(365.0, 0.35, 0.20),
        min_matches=20,
    )
    prior = build_prior_packet_from_model(
        model,
        home_team="A",
        away_team="B",
        season="2024-25",
        match_date="2024-08-20",
        calibration_ref="unit-test",
    )
    cov = np.asarray(prior["cov_log_lambda"], dtype=float)
    assert prior["status"] == "VALID"
    assert prior["source_groups"] == ["TEAM_DATA"]
    assert prior["hierarchy"]["home_team_fallback"] == "PREVIOUS_SEASON_SHRINKAGE"
    assert prior["hierarchy"]["away_team_fallback"] == "PREVIOUS_SEASON_SHRINKAGE"
    assert np.all(np.linalg.eigvalsh(cov) > 0)
    assert prior["uncertainty"]["method"] == "LAPLACE_FULL_PARAMETER_COVARIANCE_PROPAGATION"
    assert prior["anti_double_counting"]["market_inputs_used"] is False


def test_new_team_falls_back_to_league_baseline_without_fake_recent_form():
    model = fit_league_model(
        _rows(), league="德甲", as_of="2024-08-01",
        hyperparameters=HyperParameters(365.0, 0.35, 0.20), min_matches=20,
    )
    prior = build_prior_packet_from_model(
        model, home_team="NEW", away_team="A", season="2024-25", calibration_ref="unit-test"
    )
    assert prior["hierarchy"]["home_team_fallback"] == "LEAGUE_BASELINE_NEW_OR_PROMOTED_TEAM"
    assert prior["components"]["attack_home"] == 0.0
    assert prior["components"]["defense_home"] == 0.0


def test_prior_context_rejects_market_fields():
    model = fit_league_model(
        _rows(), league="德甲", as_of="2024-08-01",
        hyperparameters=HyperParameters(365.0, 0.35, 0.20), min_matches=20,
    )
    store = {
        "status": "VALID",
        "calibration_ref": "unit-test",
        "league_models": {"德甲": model},
    }
    with pytest.raises(PriorEngineError, match="Forbidden"):
        build_prior_packet(
            {
                "league": "德甲", "season": "2024-25", "home_team": "A", "away_team": "B",
                "Pinnacle_odds": [1.8, 3.8, 4.4],
            },
            store,
        )


def test_hyperparameter_selection_is_inner_season_forward_only():
    result = calibrate_hyperparameters(
        _rows(),
        league="德甲",
        train_seasons=["2021-22", "2022-23", "2023-24"],
        half_life_candidates=[180.0, 365.0],
        team_sd_candidates=[0.25, 0.5],
        transition_sd_candidates=[0.12, 0.3],
        min_matches=10,
    )
    assert result["status"] == "VALIDATED_ON_TRAIN_FOLDS"
    assert result["time_ordered"] is True
    assert set(result["selected"]) == {"half_life_days", "team_sd", "transition_sd"}
    assert result["train_seasons"] == ["2021-22", "2022-23", "2023-24"]


def test_stage14_can_auto_resolve_titan_prior_without_market_as_prior():
    model = fit_league_model(
        _rows(), league="德甲", as_of="2024-08-01",
        hyperparameters=HyperParameters(365.0, 0.35, 0.20), min_matches=20,
    )
    store = {
        "status": "VALID",
        "calibration_ref": "unit-test-store",
        "league_models": {"德甲": model},
    }
    out = automatic_top3(
        _quant_packet(),
        prior_store=store,
        prior_context={
            "league": "德甲", "season": "2024-25", "home_team": "A", "away_team": "B",
            "match_date": "2024-08-20",
        },
        draws=500,
    )
    assert out["prior_resolution"] == "AUTO_TITAN_HISTORICAL_PRIOR"
    assert out["status"] in {"BAYESIAN_POSTERIOR_TOP3", "SCORELINE_CONFLICT"}
    assert out["posterior"]["prior"]["source_groups"] == ["TEAM_DATA"]
