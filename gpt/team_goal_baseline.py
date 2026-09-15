"""Optional research bridge from MODEL_1 packets to Titan team goal baselines.

Importing this module does not alter MODEL_1 stages, priors, posterior weights,
or decisions.  Callers must opt in and treat the result as research evidence.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from research.team_goal_baselines.engine import BaselineError
from research.team_goal_baselines.runtime import TeamGoalBaselineStore


DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / "database" / "research" / "team_goal_baselines.sqlite"


def build_team_goal_baseline_packet(
    *,
    competition_id: str | None = None,
    competition: str | None = None,
    season: str | None = None,
    home_team: str,
    away_team: str,
    kickoff: str | None = None,
    match_id: str | None = None,
    quant_packet: Mapping[str, Any] | None = None,
    company: str | None = None,
    variant: str | None = None,
    database: str | Path = DEFAULT_DATABASE,
) -> dict[str, Any]:
    raw_competition = str(competition_id or competition or "")
    if not raw_competition:
        return {"status": "MISSING", "reason": "COMPETITION_REQUIRED", "research_only": True,
                "formal_model_1_weight_impact": "NONE"}
    store = TeamGoalBaselineStore(database)
    try:
        cid = store.resolve_competition(raw_competition)
        historical = store.matchup(cid, home_team, away_team, season=season, kickoff=kickoff,
                                   match_id=match_id, variant=variant)
    except BaselineError as exc:
        return {
            "status": "MISSING", "reason": "BASELINE_UNAVAILABLE", "detail": str(exc),
            "engine_version": "TITAN-BIG5-TEAM-GOAL-BASELINE-RESEARCH-1.0.0",
            "research_only": True, "formal_model_1_weight_impact": "NONE",
            "competition": raw_competition, "season": season, "home_team": home_team,
            "away_team": away_team, "kickoff": kickoff,
            "no_future_leakage": True, "baseline_fit_market_blind": True,
        }
    packet: dict[str, Any] = {
        "status": "AVAILABLE",
        "engine_version": "TITAN-BIG5-TEAM-GOAL-BASELINE-RESEARCH-1.0.0",
        "research_only": True,
        "formal_model_1_weight_impact": "NONE",
        "competition": raw_competition, "competition_id": cid, "season": season, "home_team": home_team,
        "away_team": away_team, "kickoff": kickoff,
        "selected_variant": historical["variant"],
        "half_life_days": 365.0 if historical["variant"] == "time_decay" else None,
        "history_lambda_home": historical["lambda_home"],
        "history_lambda_away": historical["lambda_away"],
        "history_total_lambda": historical["expected_total_goals"],
        "history_goal_margin": historical["expected_net_goal_difference_home"],
        "home_attack_strength": historical.get("home_attack_strength"),
        "home_defense_concede_factor": historical.get("home_defence_concession_factor"),
        "away_attack_strength": historical.get("away_attack_strength"),
        "away_defense_concede_factor": historical.get("away_defence_concession_factor"),
        "league_home_goal_baseline": historical.get("league_home_goal_baseline"),
        "league_away_goal_baseline": historical.get("league_away_goal_baseline"),
        "home_sample_size": historical.get("home_sample_games", 0.0),
        "away_sample_size": historical.get("away_sample_games", 0.0),
        "new_or_promoted_home": "PROMOTED_OR_NEW" in historical.get("home_history_class", ""),
        "new_or_promoted_away": "PROMOTED_OR_NEW" in historical.get("away_history_class", ""),
        "fallback_used": "PROMOTED_OR_NEW" in (historical.get("home_history_class", "") + historical.get("away_history_class", "")),
        "fallback_reason": {"home": historical.get("home_history_class"), "away": historical.get("away_history_class")},
        "provenance": {"source": "TITAN_COMPLETED_RESULTS", "source_sha256": historical.get("source_sha256"),
                        "baseline_fit_market_blind": True, "no_future_leakage": True,
                        "independent_from_domestic_prior": True, "overlap_scope": "RESULT_HISTORY"},
        "historical_matchup": historical,
    }
    if quant_packet is not None:
        packet["market_comparison"] = store.compare_quant_packet(historical, quant_packet, company)
        packet.update({
            "market_lambda_home": packet["market_comparison"]["market_lambda_home"],
            "market_lambda_away": packet["market_comparison"]["market_lambda_away"],
            "market_total_lambda": packet["market_comparison"]["market_total_lambda"],
            "market_goal_margin": packet["market_comparison"]["market_goal_margin"],
            "market_home_lambda_residual": packet["market_comparison"]["market_home_lambda_residual"],
            "market_away_lambda_residual": packet["market_comparison"]["market_away_lambda_residual"],
            "market_total_residual": packet["market_comparison"]["market_total_residual"],
            "market_goal_residual": packet["market_comparison"]["market_goal_residual"],
            "standardized_residuals": packet["market_comparison"]["interpretation"]["standardized_residuals"],
            "deviation_labels": packet["market_comparison"]["interpretation"]["labels"],
        })
    else:
        packet.update({"market_comparison": {"status": "MISSING", "reason": "QUANT_PACKET_UNAVAILABLE"},
                       "market_deviation_status": "MISSING"})
    return packet
