from __future__ import annotations

from datetime import datetime
import sqlite3

import pytest

from gpt.prior_competition import (
    audit_competition_coverage,
    build_competition_store,
    competition_split,
    resolve_prior,
)
from gpt.prior_engine import HyperParameters, PriorEngineError
from gpt.stage14_auto import automatic_top3


def _rows():
    rows = []
    match_id = 1
    teams = ["A", "B", "C", "D"]
    for competition, boost in (("英超", 1), ("欧冠", 0)):
        for season_i, season in enumerate(("2021-22", "2022-23", "2023-24", "2024-25", "2025-26")):
            start = 2021 + season_i
            for cycle in range(6):
                for i, home in enumerate(teams):
                    away = teams[(i + cycle + 1) % len(teams)]
                    if home == away:
                        continue
                    rows.append({
                        "match_id": str(match_id),
                        "match_date": datetime(start, 8 + min(cycle, 4), 1 + i),
                        "league": competition,
                        "season": season,
                        "season_start": start,
                        "home_team": home,
                        "away_team": away,
                        "home_score": 1 + boost + int(home in {"A", "B"}),
                        "away_score": int(away == "A"),
                    })
                    match_id += 1
    rows.sort(key=lambda r: (r["match_date"], r["match_id"]))
    return rows


def _quant_packet():
    return {
        "engine_version": "q",
        "match_id": "future-1",
        "snapshot_time": "2026-08-20T10:00:00Z",
        "reconstruction": {
            "Pinnacle": {"lambda_home": 1.8, "lambda_away": 1.05, "rho": -0.05, "max_abs_residual": 0.004},
            "Bet365": {"lambda_home": 1.75, "lambda_away": 1.10, "rho": -0.04, "max_abs_residual": 0.006},
            "Macau": {"lambda_home": 1.85, "lambda_away": 1.00, "rho": -0.06, "max_abs_residual": 0.005},
        },
    }


def test_competition_split_is_independent():
    rows = _rows()
    split = competition_split(rows, "欧冠", min_oos_seasons=4)
    assert split["status"] == "VALID"
    assert split["train"] == ["2021-22", "2022-23", "2023-24"]
    assert split["validate"] == ["2024-25"]
    assert split["test"] == ["2025-26"]


def test_competition_store_keeps_baselines_isolated():
    rows = _rows()
    hyper = {"half_life_days": 365.0, "team_sd": 0.35, "transition_sd": 0.20}
    store = build_competition_store(
        rows,
        hyperparameters_by_competition={"英超": hyper, "欧冠": hyper},
        competition_status={
            "英超": {"activation": "ACTIVE", "reason": "unit"},
            "欧冠": {"activation": "ACTIVE", "reason": "unit"},
        },
        as_of="2026-08-01",
        dataset_audit={"matches_count": len(rows), "dataset_sha256": "unit"},
        calibration={"unit": True},
        min_matches=20,
    )
    assert set(store["competition_models"]) == {"英超", "欧冠"}
    epl_mu = store["competition_models"]["英超"]["theta"][0]
    ucl_mu = store["competition_models"]["欧冠"]["theta"][0]
    assert epl_mu != pytest.approx(ucl_mu)
    assert store["legacy_field_semantics"]["mu_league"] == "competition-specific scoring baseline"


def test_active_competition_resolves_and_shadow_is_blocked():
    rows = _rows()
    hyper = {"half_life_days": 365.0, "team_sd": 0.35, "transition_sd": 0.20}
    store = build_competition_store(
        rows,
        hyperparameters_by_competition={"英超": hyper, "欧冠": hyper},
        competition_status={
            "英超": {"activation": "ACTIVE", "reason": "unit"},
            "欧冠": {"activation": "SHADOW", "reason": "unit"},
        },
        as_of="2026-08-01",
        dataset_audit={"matches_count": len(rows), "dataset_sha256": "unit"},
        calibration={"unit": True},
        min_matches=20,
    )
    prior = resolve_prior(
        {"competition": "英超", "season": "2026-27", "home_team": "A", "away_team": "B"}, store
    )
    assert prior["status"] == "VALID"
    assert prior["activation"] == "ACTIVE"
    assert prior["components"]["mu_competition"] == prior["components"]["mu_league"]
    with pytest.raises(PriorEngineError, match="not formally active"):
        resolve_prior(
            {"competition": "欧冠", "season": "2026-27", "home_team": "A", "away_team": "B"}, store
        )


def test_unsupported_competition_does_not_fall_back_to_market():
    rows = _rows()
    hyper = {"half_life_days": 365.0, "team_sd": 0.35, "transition_sd": 0.20}
    store = build_competition_store(
        rows,
        hyperparameters_by_competition={"英超": hyper},
        competition_status={"英超": {"activation": "ACTIVE", "reason": "unit"}},
        as_of="2026-08-01",
        dataset_audit={"matches_count": len(rows), "dataset_sha256": "unit"},
        calibration={"unit": True},
        min_matches=20,
    )
    out = automatic_top3(
        _quant_packet(),
        prior_store=store,
        prior_context={"competition": "未知赛事", "season": "2026-27", "home_team": "A", "away_team": "B"},
        draws=500,
    )
    assert out["status"] == "MISSING"
    assert out["reason"] == "BAYESIAN_PRIOR_UNAVAILABLE"
    assert out["no_market_only_fallback"] is True


def test_market_fields_are_rejected_in_competition_context():
    rows = _rows()
    hyper = {"half_life_days": 365.0, "team_sd": 0.35, "transition_sd": 0.20}
    store = build_competition_store(
        rows,
        hyperparameters_by_competition={"英超": hyper},
        competition_status={"英超": {"activation": "ACTIVE", "reason": "unit"}},
        as_of="2026-08-01",
        dataset_audit={"matches_count": len(rows), "dataset_sha256": "unit"},
        calibration={"unit": True},
        min_matches=20,
    )
    with pytest.raises(PriorEngineError, match="Forbidden"):
        resolve_prior({
            "competition": "英超", "season": "2026-27", "home_team": "A", "away_team": "B",
            "Pinnacle_odds": [1.8, 3.8, 4.4],
        }, store)


def test_raw_coverage_audits_every_distinct_competition(tmp_path):
    db = tmp_path / "raw.sqlite"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE matches (match_id TEXT, kickoff TEXT, competition TEXT, season TEXT, "
        "home_team TEXT, away_team TEXT, home_score INTEGER, away_score INTEGER)"
    )
    rows = [
        ("1", "2024-01-01", "英超", "2023-24", "A", "B", 2, 1),
        ("2", "2024-01-02", "欧冠", "2023-24", "C", "D", 1, 1),
        ("3", "2024-01-03", "新增赛事", "2023-24", "E", "F", None, None),
    ]
    con.executemany("INSERT INTO matches VALUES (?,?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    audit = audit_competition_coverage(db, min_completed_matches=1, min_oos_seasons=1)
    assert audit["competition_universe"] == ["新增赛事", "欧冠", "英超"]
    mapped = {x["competition"]: x for x in audit["competition_coverage"]}
    assert mapped["新增赛事"]["matches"] == 1
    assert mapped["新增赛事"]["missing_scores"] == 1
    assert mapped["欧冠"]["completed_matches"] == 1
