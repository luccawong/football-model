"""Titan-only big-five team goal baseline research engine.

The module is deliberately separate from MODEL_1's fixed weighting.  It builds
pre-match attack/concession factors from completed Titan results only and can
compare their matchup lambdas with the market lambdas already reconstructed by
MODEL_1's 1X2+OU quant layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import math
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Mapping, Sequence


ENGINE_VERSION = "TITAN-BIG5-TEAM-GOAL-BASELINE-RESEARCH-1.0.0"
FIVE_LEAGUES = {
    "36": ("英超", "epl"),
    "31": ("西甲", "laliga"),
    "34": ("意甲", "seriea"),
    "8": ("德甲", "bundesliga"),
    "11": ("法甲", "ligue1"),
}
DEFAULT_VARIANTS = {
    "five_year_mean": {"pseudo_games": 5.0},
    "recent_two_seasons": {"pseudo_games": 5.0},
    "time_decay": {"pseudo_games": 5.0, "half_life_days": 365.0},
    "current_season_history_shrinkage": {
        "history_pseudo_games": 5.0,
        "history_equivalent_games": 10.0,
    },
}


class BaselineError(ValueError):
    pass


@dataclass(frozen=True)
class Match:
    match_id: str
    competition_id: str
    competition: str
    season: str
    season_start: int
    kickoff: datetime
    home_team_id: str
    away_team_id: str
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int


def _dt(value: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            pass
    raise BaselineError(f"Unsupported kickoff: {value!r}")


def _season_start(value: str) -> int:
    text = str(value).strip().replace("/", "-")
    try:
        year = int(text[:4])
    except (TypeError, ValueError) as exc:
        raise BaselineError(f"Unsupported season: {value!r}") from exc
    if not 2000 <= year <= 2100:
        raise BaselineError(f"Unsupported season: {value!r}")
    return year


def load_completed_matches(db_path: str | Path) -> tuple[list[Match], dict[str, Any]]:
    """Load and deterministically de-duplicate completed big-five Titan matches."""
    path = Path(db_path)
    if not path.exists():
        raise BaselineError(f"Titan database not found: {path}")
    con = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "matches" not in tables:
            raise BaselineError("Titan database has no matches table")
        columns = {r[1] for r in con.execute("PRAGMA table_info(matches)")}
        required = {
            "match_id", "competition_id", "competition", "season", "kickoff",
            "home_team_id", "away_team_id", "home_team", "away_team",
            "home_score", "away_score",
        }
        missing = sorted(required - columns)
        if missing:
            raise BaselineError(f"Titan matches table missing fields: {missing}")
        raw = con.execute(
            "SELECT match_id,competition_id,competition,season,kickoff,"
            "home_team_id,away_team_id,home_team,away_team,home_score,away_score "
            "FROM matches WHERE competition_id IN ('36','31','34','8','11')"
        ).fetchall()
    finally:
        con.close()

    invalid = 0
    duplicates_match_id = 0
    duplicates_fixture = 0
    seen_ids: set[str] = set()
    seen_fixtures: set[tuple[str, str, str, str]] = set()
    matches: list[Match] = []
    for row in sorted(raw, key=lambda r: (str(r["kickoff"]), str(r["match_id"]))):
        try:
            values = dict(row)
            if any(values[k] is None or str(values[k]).strip() == "" for k in required):
                invalid += 1
                continue
            hg, ag = int(values["home_score"]), int(values["away_score"])
            if hg < 0 or ag < 0:
                invalid += 1
                continue
            match_id = str(values["match_id"])
            if match_id in seen_ids:
                duplicates_match_id += 1
                continue
            fixture_key = (
                str(values["competition_id"]), str(values["kickoff"]),
                str(values["home_team_id"]), str(values["away_team_id"]),
            )
            if fixture_key in seen_fixtures:
                duplicates_fixture += 1
                continue
            seen_ids.add(match_id)
            seen_fixtures.add(fixture_key)
            matches.append(Match(
                match_id=match_id,
                competition_id=str(values["competition_id"]),
                competition=str(values["competition"]),
                season=str(values["season"]),
                season_start=_season_start(str(values["season"])),
                kickoff=_dt(str(values["kickoff"])),
                home_team_id=str(values["home_team_id"]),
                away_team_id=str(values["away_team_id"]),
                home_team=str(values["home_team"]),
                away_team=str(values["away_team"]),
                home_goals=hg,
                away_goals=ag,
            ))
        except (TypeError, ValueError, BaselineError):
            invalid += 1
    return matches, {
        "source_rows_big5": len(raw),
        "usable_matches_big5": len(matches),
        "excluded_invalid_or_missing_result": invalid,
        "excluded_duplicate_match_id": duplicates_match_id,
        "excluded_duplicate_fixture": duplicates_fixture,
        "competition_ids": sorted(FIVE_LEAGUES),
    }


def _weight(match: Match, *, variant: str, as_of: datetime, season_start: int,
            params: Mapping[str, float]) -> float:
    if match.kickoff >= as_of:
        return 0.0
    if variant == "five_year_mean":
        return 1.0
    if variant == "recent_two_seasons":
        return 1.0 if match.season_start >= season_start - 1 else 0.0
    if variant == "time_decay":
        age = max(0.0, (as_of - match.kickoff).total_seconds() / 86400.0)
        return 0.5 ** (age / float(params["half_life_days"]))
    if variant == "current_season_history_shrinkage":
        return 1.0
    raise BaselineError(f"Unknown variant: {variant}")


def _empty_stats() -> dict[str, float]:
    return {"games": 0.0, "gf": 0.0, "ga": 0.0}


def _accumulate(rows: Iterable[Match], weights: Iterable[float]) -> tuple[dict[str, float], dict[str, dict[str, dict[str, float]]]]:
    league = {"games": 0.0, "home_goals": 0.0, "away_goals": 0.0}
    team: dict[str, dict[str, dict[str, float]]] = {}
    for m, w in zip(rows, weights):
        if w <= 0:
            continue
        league["games"] += w
        league["home_goals"] += w * m.home_goals
        league["away_goals"] += w * m.away_goals
        hs = team.setdefault(m.home_team_id, {"all": _empty_stats(), "home": _empty_stats(), "away": _empty_stats()})
        aw = team.setdefault(m.away_team_id, {"all": _empty_stats(), "home": _empty_stats(), "away": _empty_stats()})
        for bucket, gf, ga in ((hs["all"], m.home_goals, m.away_goals), (hs["home"], m.home_goals, m.away_goals),
                               (aw["all"], m.away_goals, m.home_goals), (aw["away"], m.away_goals, m.home_goals)):
            bucket["games"] += w
            bucket["gf"] += w * gf
            bucket["ga"] += w * ga
    return league, team


def _rate(goals: float, games: float, baseline: float, pseudo_games: float) -> float:
    return (goals + pseudo_games * baseline) / max(1e-12, games + pseudo_games)


def build_snapshot(rows: Sequence[Match], *, as_of: datetime, season_start: int,
                   variant: str, params: Mapping[str, float]) -> dict[str, Any]:
    """Build one leakage-safe league snapshot from matches strictly before as_of."""
    eligible = [m for m in rows if m.kickoff < as_of]
    if not eligible:
        raise BaselineError("No pre-cutoff history")
    weights = [_weight(m, variant=variant, as_of=as_of, season_start=season_start, params=params) for m in eligible]
    league, teams = _accumulate(eligible, weights)
    if league["games"] <= 0:
        raise BaselineError("No weighted pre-cutoff history")
    home_avg = league["home_goals"] / league["games"]
    away_avg = league["away_goals"] / league["games"]
    total_avg = home_avg + away_avg

    if variant == "current_season_history_shrinkage":
        prior_rows = [m for m in eligible if m.season_start < season_start]
        current_rows = [m for m in eligible if m.season_start == season_start]
        prior_league, prior_teams = _accumulate(prior_rows, [1.0] * len(prior_rows))
        current_league, current_teams = _accumulate(current_rows, [1.0] * len(current_rows))
        if prior_league["games"] > 0:
            hist_home = prior_league["home_goals"] / prior_league["games"]
            hist_away = prior_league["away_goals"] / prior_league["games"]
        else:
            hist_home, hist_away = home_avg, away_avg
        if current_league["games"] > 0:
            home_avg = (current_league["home_goals"] + float(params["history_equivalent_games"]) * hist_home) / (current_league["games"] + float(params["history_equivalent_games"]))
            away_avg = (current_league["away_goals"] + float(params["history_equivalent_games"]) * hist_away) / (current_league["games"] + float(params["history_equivalent_games"]))
            total_avg = home_avg + away_avg
        merged: dict[str, dict[str, dict[str, float]]] = {}
        team_ids = set(prior_teams) | set(current_teams)
        for team_id in team_ids:
            merged[team_id] = {}
            for venue, attack_base, defence_base in (("home", hist_home, hist_away), ("away", hist_away, hist_home), ("all", total_avg / 2.0, total_avg / 2.0)):
                h = prior_teams.get(team_id, {}).get(venue, _empty_stats())
                c = current_teams.get(team_id, {}).get(venue, _empty_stats())
                hp = float(params.get("history_pseudo_games", 5.0))
                eq = float(params["history_equivalent_games"])
                hgf = _rate(h["gf"], h["games"], attack_base, hp)
                hga = _rate(h["ga"], h["games"], defence_base, hp)
                merged[team_id][venue] = {
                    "games": c["games"] + eq,
                    "observed_games": c["games"],
                    "gf": c["gf"] + eq * hgf,
                    "ga": c["ga"] + eq * hga,
                }
        teams = merged

    pseudo = float(params.get("pseudo_games", 0.0))
    output: dict[str, Any] = {
        "variant": variant,
        "params": dict(params),
        "as_of": as_of.isoformat(sep=" "),
        "season_start": season_start,
        "league_games_effective": league["games"],
        "league_home_goals_per_match": home_avg,
        "league_away_goals_per_match": away_avg,
        "league_total_goals_per_match": total_avg,
        "teams": {},
    }
    prior_ids = {
        team_id for m in eligible if m.season_start < season_start
        for team_id in (m.home_team_id, m.away_team_id)
    }
    current_ids = {
        team_id for m in eligible if m.season_start == season_start
        for team_id in (m.home_team_id, m.away_team_id)
    }
    for team_id, venue_stats in teams.items():
        home = venue_stats["home"]
        away = venue_stats["away"]
        overall = venue_stats["all"]
        home_gf = _rate(home["gf"], home["games"], home_avg, pseudo)
        home_ga = _rate(home["ga"], home["games"], away_avg, pseudo)
        away_gf = _rate(away["gf"], away["games"], away_avg, pseudo)
        away_ga = _rate(away["ga"], away["games"], home_avg, pseudo)
        all_base = total_avg / 2.0
        output["teams"][team_id] = {
            "games": overall.get("observed_games", overall["games"]),
            "gf": overall["gf"], "ga": overall["ga"],
            "gf_per_game": _rate(overall["gf"], overall["games"], all_base, pseudo),
            "ga_per_game": _rate(overall["ga"], overall["games"], all_base, pseudo),
            "home_games": home.get("observed_games", home["games"]),
            "home_gf": home["gf"], "home_ga": home["ga"],
            "home_gf_per_game": home_gf, "home_ga_per_game": home_ga,
            "away_games": away.get("observed_games", away["games"]),
            "away_gf": away["gf"], "away_ga": away["ga"],
            "away_gf_per_game": away_gf, "away_ga_per_game": away_ga,
            "home_attack_strength": home_gf / home_avg,
            "home_defence_concession_factor": home_ga / away_avg,
            "away_attack_strength": away_gf / away_avg,
            "away_defence_concession_factor": away_ga / home_avg,
            "history_class": (
                "RETURNING_OR_CONTINUING_TEAM_HISTORY" if team_id in prior_ids else
                "PROMOTED_OR_NEW_LEAGUE_BASELINE" if team_id in current_ids else
                "UNKNOWN_TEAM_LEAGUE_BASELINE"
            ),
        }
    return output


def matchup_lambda(snapshot: Mapping[str, Any], home_team_id: str, away_team_id: str) -> dict[str, Any]:
    """Return venue-adjusted matchup lambdas and expected total/margin."""
    teams = snapshot["teams"]
    home = teams.get(str(home_team_id))
    away = teams.get(str(away_team_id))
    home_avg = float(snapshot["league_home_goals_per_match"])
    away_avg = float(snapshot["league_away_goals_per_match"])
    if home is None:
        home = {"home_attack_strength": 1.0, "home_defence_concession_factor": 1.0,
                "history_class": "PROMOTED_OR_NEW_LEAGUE_BASELINE", "home_games": 0.0}
    if away is None:
        away = {"away_attack_strength": 1.0, "away_defence_concession_factor": 1.0,
                "history_class": "PROMOTED_OR_NEW_LEAGUE_BASELINE", "away_games": 0.0}
    lh = home_avg * float(home["home_attack_strength"]) * float(away["away_defence_concession_factor"])
    la = away_avg * float(away["away_attack_strength"]) * float(home["home_defence_concession_factor"])
    lh, la = min(6.0, max(0.05, lh)), min(6.0, max(0.05, la))
    return {
        "lambda_home": lh,
        "lambda_away": la,
        "expected_total_goals": lh + la,
        "expected_net_goal_difference_home": lh - la,
        "home_history_class": home["history_class"],
        "away_history_class": away["history_class"],
        "home_sample_games": home.get("home_games", 0.0),
        "away_sample_games": away.get("away_games", 0.0),
        "variant": snapshot["variant"],
        "as_of": snapshot["as_of"],
    }


def compare_market_lambda(historical: Mapping[str, float], market: Mapping[str, float]) -> dict[str, float]:
    """Compare historical matchup lambda to MODEL_1's Titan 1X2+OU lambda.

    ``market_goal_residual`` is the market-minus-history expected home margin.
    Positive means the market makes the home side stronger than history does.
    ``market_total_residual`` is market-minus-history expected total goals.
    """
    hh, ha = float(historical["lambda_home"]), float(historical["lambda_away"])
    mh = float(market["lambda_home"])
    ma = float(market["lambda_away"])
    return {
        "market_home_lambda_residual": mh - hh,
        "market_away_lambda_residual": ma - ha,
        "market_goal_residual": (mh - ma) - (hh - ha),
        "market_total_residual": (mh + ma) - (hh + ha),
        "historical_expected_margin": hh - ha,
        "market_expected_margin": mh - ma,
        "historical_expected_total": hh + ha,
        "market_expected_total": mh + ma,
    }


def classify_team_goal_market_deviation(
    packet: Mapping[str, Any],
    calibration: Mapping[str, Mapping[str, float]] | None = None,
) -> dict[str, Any]:
    """Interpret market-vs-history deviations without changing any lambda.

    Calibration is league-specific and must be produced from the training split.
    A missing calibration is explicit and never replaced by a fixed universal
    threshold.
    """
    raw_keys = {
        "home": "market_home_lambda_residual",
        "away": "market_away_lambda_residual",
        "total": "market_total_residual",
        "margin": "market_goal_residual",
    }
    standardized: dict[str, float | None] = {}
    magnitude: dict[str, str] = {}
    labels: list[str] = []
    for axis, key in raw_keys.items():
        value = float(packet[key])
        row = (calibration or {}).get(axis)
        if not row or not row.get("robust_sd") or float(row["robust_sd"]) <= 0:
            standardized["z_robust_" + axis] = None
            magnitude[axis] = "UNSTANDARDIZED"
            continue
        median = float(row.get("median", 0.0))
        z = (value - median) / float(row["robust_sd"])
        standardized["z_robust_" + axis] = z
        az = abs(z)
        magnitude[axis] = "EXTREME" if az >= 3.0 else "LARGE" if az >= 2.0 else "MODERATE" if az >= 1.0 else "SMALL"

    home = float(packet["market_home_lambda_residual"])
    away = float(packet["market_away_lambda_residual"])
    total = float(packet["market_total_residual"])
    margin = float(packet["market_goal_residual"])
    def _direction(axis: str, positive: str, negative: str) -> None:
        z = standardized.get("z_robust_" + axis)
        if z is None:
            return
        if abs(float(z)) >= 1.0:
            labels.append(positive if float(z) > 0 else negative)

    _direction("home", "HOME_ATTACK_MARKUP", "HOME_ATTACK_DISCOUNT")
    _direction("away", "AWAY_ATTACK_MARKUP", "AWAY_ATTACK_DISCOUNT")
    _direction("total", "TOTAL_MARKUP", "TOTAL_DISCOUNT")
    _direction("margin", "HOME_MARGIN_MARKUP", "AWAY_MARGIN_MARKUP")
    if not labels:
        labels.append("NEAR_BASELINE")
    elif all(magnitude.get(axis) == "SMALL" for axis in raw_keys):
        labels.append("NEAR_BASELINE")
    return {
        "labels": labels,
        "magnitude_by_axis": magnitude,
        "standardized_residuals": standardized,
        "calibration_status": "TRAIN_ONLY" if calibration else "MISSING_TRAIN_CALIBRATION",
        "lambda_unchanged": True,
    }


def poisson_nll(goals: int, rate: float) -> float:
    return rate - goals * math.log(rate) + math.lgamma(goals + 1.0)


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
