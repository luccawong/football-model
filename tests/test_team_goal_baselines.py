from datetime import datetime

import pytest

from research.team_goal_baselines.engine import BaselineError, Match, build_snapshot, classify_team_goal_market_deviation, compare_market_lambda, matchup_lambda
from research.team_goal_baselines.runtime import TeamGoalBaselineStore


def m(mid, season, date, home, away, hg, ag):
    return Match(str(mid), "36", "英超", season, int(season[:4]), datetime.fromisoformat(date),
                 home, away, home, away, hg, ag)


def test_matchup_is_strictly_pre_cutoff_and_has_expected_identity_baseline():
    rows = [
        m(1, "2021-2022", "2021-08-01 15:00", "A", "B", 2, 0),
        m(2, "2021-2022", "2021-08-08 15:00", "B", "A", 1, 1),
        m(3, "2022-2023", "2022-08-01 15:00", "A", "C", 6, 6),
    ]
    snap = build_snapshot(rows, as_of=datetime(2022, 8, 1, 15), season_start=2022,
                          variant="five_year_mean", params={"pseudo_games": 5.0})
    assert snap["league_games_effective"] == 2
    pred = matchup_lambda(snap, "A", "C")
    assert pred["away_history_class"] == "PROMOTED_OR_NEW_LEAGUE_BASELINE"
    assert pred["lambda_home"] > pred["lambda_away"]


def test_current_season_history_shrinkage_handles_promoted_team():
    rows = [
        m(1, "2021-2022", "2021-08-01 15:00", "A", "B", 2, 0),
        m(2, "2022-2023", "2022-08-01 15:00", "C", "A", 1, 1),
    ]
    snap = build_snapshot(rows, as_of=datetime(2022, 8, 2), season_start=2022,
                          variant="current_season_history_shrinkage",
                          params={"history_pseudo_games": 5.0, "history_equivalent_games": 10.0})
    assert snap["teams"]["C"]["history_class"] == "PROMOTED_OR_NEW_LEAGUE_BASELINE"
    assert snap["teams"]["C"]["home_games"] == 1


def test_market_residual_semantics():
    out = compare_market_lambda({"lambda_home": 1.4, "lambda_away": 1.0},
                                {"lambda_home": 1.8, "lambda_away": 1.1})
    assert out["market_total_residual"] == pytest.approx(0.5)
    assert out["market_goal_residual"] == pytest.approx(0.3)


def test_deviation_labels_use_league_train_calibration_and_do_not_change_lambdas():
    raw = compare_market_lambda({"lambda_home": 1.4, "lambda_away": 1.0},
                                {"lambda_home": 1.8, "lambda_away": 1.1})
    interpretation = classify_team_goal_market_deviation(raw, {
        "home": {"robust_sd": .1}, "away": {"robust_sd": .1},
        "total": {"robust_sd": .1}, "margin": {"robust_sd": .1},
    })
    assert "HOME_ATTACK_MARKUP" in interpretation["labels"]
    assert "TOTAL_MARKUP" in interpretation["labels"]
    assert interpretation["calibration_status"] == "TRAIN_ONLY"
    assert interpretation["lambda_unchanged"] is True


def test_robust_z_is_centered_on_nonzero_train_median():
    packet = compare_market_lambda({"lambda_home": 1.4, "lambda_away": 1.0},
                                   {"lambda_home": 1.8, "lambda_away": 1.1})
    calibration = {axis: {"median": value, "robust_sd": .2}
                   for axis, value in {"home": .4, "away": .1, "total": .5, "margin": .3}.items()}
    out = classify_team_goal_market_deviation(packet, calibration)
    assert out["standardized_residuals"] == {
        "z_robust_home": pytest.approx(0.0), "z_robust_away": pytest.approx(0.0),
        "z_robust_total": pytest.approx(0.0), "z_robust_margin": pytest.approx(0.0),
    }
    assert out["labels"] == ["NEAR_BASELINE"]


def test_small_calibrated_deviation_is_not_markup():
    packet = compare_market_lambda({"lambda_home": 1.4, "lambda_away": 1.0},
                                   {"lambda_home": 1.81, "lambda_away": 1.1})
    calibration = {axis: {"median": 0.0, "robust_sd": 1.0}
                   for axis in ("home", "away", "total", "margin")}
    out = classify_team_goal_market_deviation(packet, calibration)
    assert out["labels"] == ["NEAR_BASELINE"]


def test_provenance_distinguishes_pipeline_and_evidence_overlap():
    from gpt.team_goal_baseline import build_team_goal_baseline_packet
    import sqlite3
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as directory:
        db = __import__("pathlib").Path(directory) / "b.sqlite"
        with sqlite3.connect(db) as con:
            con.executescript("""
            CREATE TABLE team_aliases(competition_id TEXT,team_id TEXT,alias TEXT,appearances INTEGER);
            CREATE TABLE selected_variants(competition_id TEXT,selected_variant TEXT);
            CREATE TABLE latest_league_baselines(competition_id TEXT,competition TEXT,variant TEXT,as_of TEXT,home_goals_per_match REAL,away_goals_per_match REAL);
            CREATE TABLE latest_team_baselines(competition_id TEXT,variant TEXT,team_id TEXT,history_class TEXT,home_attack_strength REAL,home_defence_concession_factor REAL,away_attack_strength REAL,away_defence_concession_factor REAL);
            INSERT INTO team_aliases VALUES ('36','1','主队',10),('36','2','客队',10);
            INSERT INTO selected_variants VALUES ('36','time_decay');
            INSERT INTO latest_league_baselines VALUES ('36','英超','time_decay','2026-05-31 00:00',1.5,1.2);
            INSERT INTO latest_team_baselines VALUES ('36','time_decay','1','H',1.1,0.9,1.0,1.0),('36','time_decay','2','A',1.0,1.0,1.2,1.1);
            """)
        con.close()
        packet = build_team_goal_baseline_packet(database=db, competition_id="36", home_team="主队", away_team="客队")
        assert packet["provenance"]["pipeline_independent_from_domestic_prior"] is True
        assert packet["provenance"]["evidence_independent_from_domestic_prior"] is False
        assert packet["provenance"]["overlap_scope"] == "RESULT_HISTORY"
        assert packet["provenance"]["do_not_double_count_as_independent_prior"] is True


def test_runtime_market_packet(tmp_path):
    import sqlite3
    db = tmp_path / "b.sqlite"
    with sqlite3.connect(db) as con:
        con.executescript("""
        CREATE TABLE team_aliases(competition_id TEXT,team_id TEXT,alias TEXT,appearances INTEGER);
        CREATE TABLE selected_variants(competition_id TEXT,selected_variant TEXT);
        CREATE TABLE latest_league_baselines(competition_id TEXT,competition TEXT,variant TEXT,as_of TEXT,home_goals_per_match REAL,away_goals_per_match REAL);
        CREATE TABLE latest_team_baselines(competition_id TEXT,variant TEXT,team_id TEXT,history_class TEXT,home_attack_strength REAL,home_defence_concession_factor REAL,away_attack_strength REAL,away_defence_concession_factor REAL);
        INSERT INTO team_aliases VALUES ('36','1','主队',10),('36','2','客队',10);
        INSERT INTO selected_variants VALUES ('36','time_decay');
        INSERT INTO latest_league_baselines VALUES ('36','英超','time_decay','2026-05-31 00:00',1.5,1.2);
        INSERT INTO latest_team_baselines VALUES ('36','time_decay','1','H',1.1,0.9,1.0,1.0),('36','time_decay','2','A',1.0,1.0,1.2,1.1);
        """)
    store = TeamGoalBaselineStore(db)
    hist = store.matchup("36", "主队", "客队")
    recon = {
        name: {"lambda_home": 2.0 + i * .01, "lambda_away": 1.0 + i * .01}
        for i, name in enumerate(("Pinnacle", "Bet365", "Macau", "William Hill", "Ladbrokes", "Interwetten"))
    }
    comp = store.compare_quant_packet(hist, {"reconstruction": recon})
    assert comp["research_only"] is True
    assert "market_goal_residual" in comp
    assert comp["market_companies"] == ["Pinnacle", "Bet365", "Macau"]
    assert comp["market_aggregation"] == "CORRELATED_MARKET_CLUSTER_LOG_RATE_CENTER"
    reduced = {k: v for k, v in recon.items() if k in {"Pinnacle", "Bet365", "Macau"}}
    comp_reduced = store.compare_quant_packet(hist, {"reconstruction": reduced})
    assert comp["market_total_residual"] == pytest.approx(comp_reduced["market_total_residual"])
    assert comp["market_goal_residual"] == pytest.approx(comp_reduced["market_goal_residual"])


def test_strict_cutoff_requires_exact_pre_kickoff_snapshot():
    import sqlite3
    db = "database/research/team_goal_baselines.sqlite"
    with sqlite3.connect(db) as con:
        row = con.execute(
            "SELECT match_id, home_team_id, away_team_id, kickoff, lambda_home, lambda_away "
            "FROM backtest_predictions WHERE competition_id='36' AND variant='time_decay' "
            "AND split='test' ORDER BY kickoff LIMIT 1"
        ).fetchone()
        latest = con.execute(
            "SELECT as_of FROM latest_league_baselines WHERE competition_id='36' AND variant='time_decay'"
        ).fetchone()[0]
    store = TeamGoalBaselineStore(db)
    old = store.matchup("36", str(row[1]), str(row[2]), kickoff=row[3], match_id=str(row[0]))
    assert old["source"] == "BACKTEST_STRICT_KICKOFF"
    assert old["lambda_home"] == pytest.approx(row[4])
    assert old["lambda_away"] == pytest.approx(row[5])
    with pytest.raises(BaselineError, match="NO_STRICT_PRE_KICKOFF_SNAPSHOT"):
        store.matchup("36", str(row[1]), str(row[2]), kickoff=row[3], match_id="unknown-match-id")
    with pytest.raises(BaselineError, match="NO_STRICT_PRE_KICKOFF_SNAPSHOT"):
        store.matchup("36", str(row[1]), str(row[2]), kickoff=row[3])
    future = store.matchup("36", str(row[1]), str(row[2]), kickoff="2099-01-01 00:00")
    assert future["source"] == "LATEST_AS_OF_DATABASE"
    assert latest < "2099-01-01 00:00"
