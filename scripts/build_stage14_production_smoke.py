"""Build six result-blind production smoke cases from the audited Titan SQLite."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3

from gpt.prior_competition import file_sha256
from gpt.prior_engine import HyperParameters, _utc_naive, build_prior_packet_from_model, fit_league_model, load_titan_matches
from gpt.quant_core import build_quant_packet
from gpt.stage14_auto import resolve_score_engine
from gpt.stage14_bayesian import build_market_cluster_likelihood
from scripts.validate_domestic_prior_v2 import Archive, RAW_SHA

MATCHES = {
    "英超": "2789129",
    "西甲": "2804299",
    "意甲": "2784485",
    "德甲": "2799407",
    "法甲": "2800027",
    "欧冠": "2788747",
}


def build(db_path: str, prior_store: str, prior_manifest: str, output: str, *, draws: int = 4000):
    if file_sha256(db_path) != RAW_SHA:
        raise ValueError("Titan mother-source SHA256 mismatch")
    archive = Archive(db_path)
    manifest = json.loads(Path(prior_manifest).read_text(encoding="utf-8"))
    rows, _ = load_titan_matches(db_path)
    connection = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    cases = []
    try:
        for competition, match_id in MATCHES.items():
            row = connection.execute(
                "SELECT match_id, competition, season, kickoff, home_team, away_team, page_ah_line_raw "
                "FROM matches WHERE CAST(match_id AS TEXT)=?", (match_id,)
            ).fetchone()
            if row is None or str(row["competition"]) != competition:
                raise ValueError(f"Smoke match metadata mismatch: {competition}/{match_id}")
            market_payload, archived_ah = archive.payload(match_id, "closing")
            quant = build_quant_packet(market_payload)
            market = build_market_cluster_likelihood(quant)
            if market.get("status") != "VALID" or archived_ah is None:
                raise ValueError(f"Smoke market/AH unavailable: {competition}/{match_id}")
            mean = market["mean_log_lambda"]
            favorite = "HOME" if float(mean[0]) >= float(mean[1]) else "AWAY"
            execution_path = {
                "winner": favorite,
                "ah": {
                    "formal": True,
                    "backing": favorite,
                    "home_handicap": (
                        -abs(float(archived_ah)) if favorite == "HOME" else abs(float(archived_ah))
                    ),
                },
            }
            smoke_prior = None
            if competition == "欧冠":
                frozen = manifest["hyperparameters"][competition]
                model = fit_league_model(
                    rows,
                    league=competition,
                    as_of=str(row["kickoff"]),
                    hyperparameters=HyperParameters(
                        float(frozen["half_life_days"]),
                        float(frozen["team_sd"]),
                        float(frozen["transition_sd"]),
                    ),
                )
                smoke_prior = build_prior_packet_from_model(
                    model,
                    home_team=str(row["home_team"]),
                    away_team=str(row["away_team"]),
                    season=str(row["season"]),
                    match_date=str(row["kickoff"]),
                    calibration_ref="MODEL_1-TITAN-PRIOR-20260912:POINT_IN_TIME_SMOKE",
                )
                process = manifest["process_covariance"][competition]["process_cov_log_lambda"]
                smoke_prior["cov_log_lambda"] = [
                    [float(smoke_prior["cov_log_lambda"][i][j]) + float(process[i][j]) for j in range(2)]
                    for i in range(2)
                ]
                smoke_prior["activation"] = "ACTIVE"
                smoke_prior["uncertainty"]["process_cov_log_lambda"] = process
                smoke_prior["uncertainty"]["process_covariance_train_only"] = True
            result = resolve_score_engine(
                competition, str(row["season"]), str(row["home_team"]), str(row["away_team"]),
                str(row["kickoff"]), quant, snapshot_phase="closing", mode="AUTO",
                prior_store=prior_store, prior_packet=smoke_prior,
                execution_path=execution_path, draws=draws,
            )
            expected_mode = "HISTORICAL_BAYESIAN" if competition == "欧冠" else "MARKET_ONLY_FORMAL"
            if result.get("score_engine_mode") != expected_mode or len(result.get("top3", [])) != 3:
                raise ValueError(f"Production smoke failed: {competition}: {result}")
            cases.append({
                "competition": competition,
                "match_id": match_id,
                "season": str(row["season"]),
                "kickoff": str(row["kickoff"]),
                "home_team": str(row["home_team"]),
                "away_team": str(row["away_team"]),
                "snapshot_phase": "closing",
                "market_payload": market_payload,
                "market_packet_provenance": "TITAN_ARCHIVED_CLOSING_1X2_OU",
                "archived_ah_reference": archived_ah,
                "formal_execution_path": execution_path,
                "formal_execution_path_source": "PREGAME_MARKET_FAVORITE_AND_ARCHIVED_AH_MAGNITUDE",
                "historical_prior_packet": smoke_prior,
                "historical_prior_state_not_later_than_kickoff": (
                    smoke_prior is None
                    or _utc_naive(smoke_prior["state_as_of"]) <= _utc_naive(row["kickoff"])
                ),
                "result": {
                    key: result.get(key) for key in (
                        "status", "score_engine_mode", "prior_used", "historical_prior_activation",
                        "market_cluster_status", "market_companies_used", "mean_log_lambda",
                        "cov_log_lambda", "lambda_home", "lambda_away", "rho", "raw_top10",
                        "execution_filtered_top3", "Top1", "Top2", "Top3", "model_1x2",
                        "OU_references", "five_plus_home_tail", "five_plus_away_tail",
                        "execution_path", "AH_gate_status", "snapshot_phase", "provenance",
                        "no_fake_historical_prior", "anti_double_counting", "prior_usefulness_gate",
                    )
                },
            })
    finally:
        connection.close()
    payload = {
        "artifact_version": "MODEL_1-STAGE14-PRODUCTION-SMOKE-1.0.0",
        "source_sha256": RAW_SHA,
        "source_raw_matches": 13090,
        "result_fields_excluded": ["home_score", "away_score", "actual_score", "actual_result"],
        "routing_smoke_not_historical_accuracy_evaluation": True,
        "draws": draws,
        "cases": cases,
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--prior-store", default="database/priors/model_1_titan_prior_store.json")
    parser.add_argument("--prior-manifest", default="database/priors/model_1_titan_prior_manifest.json")
    parser.add_argument("--output", default="docs/data/stage14_production_smoke.json")
    parser.add_argument("--draws", type=int, default=4000)
    args = parser.parse_args()
    build(args.db, args.prior_store, args.prior_manifest, args.output, draws=args.draws)
