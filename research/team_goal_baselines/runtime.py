"""Read-only runtime over the generated team baseline SQLite artifact."""
from __future__ import annotations

import json
import math
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Any, Mapping

from .engine import BaselineError, classify_team_goal_market_deviation, compare_market_lambda


def _parse_kickoff(value: Any) -> datetime | None:
    if value is None or str(value).strip() == "":
        return None
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise BaselineError(f"Invalid kickoff datetime: {value}") from exc


class TeamGoalBaselineStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.exists():
            raise BaselineError(f"Baseline database not found: {self.path}")

    @contextmanager
    def _connect(self):
        con = sqlite3.connect(f"file:{self.path.resolve()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        try:
            yield con
        finally:
            con.close()

    def resolve_team(self, competition_id: str, name_or_id: str) -> str:
        value = str(name_or_id)
        with self._connect() as con:
            exact = con.execute(
                "SELECT team_id FROM team_aliases WHERE competition_id=? AND (team_id=? OR alias=?) "
                "ORDER BY appearances DESC, team_id LIMIT 2", (str(competition_id), value, value),
            ).fetchall()
        ids = sorted({str(r[0]) for r in exact})
        if len(ids) != 1:
            raise BaselineError(f"Team mapping is not unique: {competition_id} / {name_or_id}")
        return ids[0]

    def resolve_competition(self, competition_id_or_name: str) -> str:
        value = str(competition_id_or_name)
        if value in {"36", "31", "34", "8", "11"}:
            return value
        with self._connect() as con:
            rows = con.execute(
                "SELECT DISTINCT competition_id FROM latest_league_baselines WHERE competition=? OR competition_id=?",
                (value, value),
            ).fetchall()
        ids = sorted({str(r[0]) for r in rows})
        if len(ids) != 1:
            raise BaselineError(f"Competition mapping is not unique: {value}")
        return ids[0]

    def matchup(self, competition_id: str, home_team: str, away_team: str,
                *, season: str | None = None, kickoff: str | None = None,
                match_id: str | None = None, variant: str | None = None) -> dict[str, Any]:
        cid = str(competition_id)
        hid, aid = self.resolve_team(cid, home_team), self.resolve_team(cid, away_team)
        with self._connect() as con:
            if variant is None:
                row = con.execute("SELECT selected_variant FROM selected_variants WHERE competition_id=?", (cid,)).fetchone()
                if row is None:
                    raise BaselineError(f"No selected variant for competition: {cid}")
                variant = str(row[0])
            league = con.execute(
                "SELECT * FROM latest_league_baselines WHERE competition_id=? AND variant=?", (cid, variant),
            ).fetchone()
            teams = con.execute(
                "SELECT * FROM latest_team_baselines WHERE competition_id=? AND variant=? AND team_id IN (?,?)",
                (cid, variant, hid, aid),
            ).fetchall()
            latest_as_of = str(league["as_of"]) if league is not None and "as_of" in league.keys() else None
            strict_row = None
            if match_id is not None:
                strict_row = con.execute(
                    "SELECT * FROM backtest_predictions WHERE match_id=? AND competition_id=? AND variant=? "
                    "AND home_team_id=? AND away_team_id=?",
                    (str(match_id), cid, variant, hid, aid),
                ).fetchone()
        if league is None:
            raise BaselineError(f"No latest baseline: {cid} / {variant}")
        requested_dt = _parse_kickoff(kickoff)
        latest_dt = _parse_kickoff(latest_as_of)
        historical_request = requested_dt is not None and latest_dt is not None and requested_dt < latest_dt
        if strict_row is not None and requested_dt is not None:
            strict_dt = _parse_kickoff(strict_row["kickoff"])
            if strict_dt is None or strict_dt != requested_dt:
                strict_row = None
        if historical_request and strict_row is None:
            raise BaselineError("NO_STRICT_PRE_KICKOFF_SNAPSHOT")
        by_id = {str(r["team_id"]): dict(r) for r in teams}
        home = by_id.get(hid, {})
        away = by_id.get(aid, {})
        if strict_row is not None:
            lh = float(strict_row["lambda_home"])
            la = float(strict_row["lambda_away"])
            source = "BACKTEST_STRICT_KICKOFF"
            effective_kickoff = str(strict_row["kickoff"])
            home_class = str(strict_row["home_history_class"])
            away_class = str(strict_row["away_history_class"])
            home_samples = float(strict_row["home_sample_games"])
            away_samples = float(strict_row["away_sample_games"])
        else:
            lh = float(league["home_goals_per_match"]) * float(home.get("home_attack_strength", 1.0)) * float(away.get("away_defence_concession_factor", 1.0))
            la = float(league["away_goals_per_match"]) * float(away.get("away_attack_strength", 1.0)) * float(home.get("home_defence_concession_factor", 1.0))
            source = "LATEST_AS_OF_DATABASE"
            effective_kickoff = kickoff
            home_class = home.get("history_class", "PROMOTED_OR_NEW_LEAGUE_BASELINE")
            away_class = away.get("history_class", "PROMOTED_OR_NEW_LEAGUE_BASELINE")
            home_samples = float(home.get("home_matches", 0.0))
            away_samples = float(away.get("away_matches", 0.0))
        lh, la = min(6.0, max(0.05, lh)), min(6.0, max(0.05, la))
        selected = dict(league)
        return {
            "competition_id": cid, "variant": variant,
            "season": season, "kickoff": effective_kickoff,
            "home_team_id": hid, "away_team_id": aid,
            "lambda_home": lh, "lambda_away": la,
            "expected_total_goals": lh + la,
            "expected_net_goal_difference_home": lh - la,
            "home_history_class": home_class,
            "away_history_class": away_class,
            "home_sample_games": home_samples, "away_sample_games": away_samples,
            "home_attack_strength": home.get("home_attack_strength"),
            "home_defence_concession_factor": home.get("home_defence_concession_factor"),
            "away_attack_strength": away.get("away_attack_strength"),
            "away_defence_concession_factor": away.get("away_defence_concession_factor"),
            "league_home_goal_baseline": float(selected["home_goals_per_match"]),
            "league_away_goal_baseline": float(selected["away_goals_per_match"]),
            "source": source,
            "source_sha256": self.source_sha256(),
            "research_only": True,
        }

    def source_sha256(self) -> str:
        try:
            with self._connect() as con:
                row = con.execute("SELECT value_json FROM metadata WHERE key='source_sha256'").fetchone()
        except sqlite3.Error:
            return ""
        return json.loads(row[0]) if row else ""

    def _calibration(self, competition_id: str) -> dict[str, dict[str, float]]:
        try:
            with self._connect() as con:
                rows = con.execute(
                    "SELECT axis, median, mad, robust_sd, p10, p25, p75, p90 FROM market_residual_calibration WHERE competition_id=?",
                    (str(competition_id),),
                ).fetchall()
        except sqlite3.Error:
            return {}
        return {str(r["axis"]): dict(r) for r in rows}

    def compare_quant_packet(self, historical: Mapping[str, float], quant_packet: Mapping[str, Any],
                             company: str | None = None) -> dict[str, Any]:
        recon = quant_packet.get("reconstruction", {})
        if not isinstance(recon, Mapping) or not recon:
            raise BaselineError("Quant packet has no Titan 1X2+OU reconstruction")
        if company is not None:
            selected = recon.get(company)
            companies = [company]
        else:
            from gpt.stage14_bayesian import build_market_cluster_likelihood
            cluster = build_market_cluster_likelihood(quant_packet)
            if cluster.get("status") != "VALID":
                raise BaselineError("Quant packet has no usable core market cluster")
            selected = {"lambda_home": float(cluster["mean_lambda"][0]), "lambda_away": float(cluster["mean_lambda"][1])}
            companies = list(cluster.get("companies_used", []))
        if not isinstance(selected, Mapping):
            raise BaselineError(f"Company reconstruction unavailable: {company}")
        result = compare_market_lambda(historical, selected)
        result.update({
            "market_lambda_home": result["market_home_lambda_residual"] + float(historical["lambda_home"]),
            "market_lambda_away": result["market_away_lambda_residual"] + float(historical["lambda_away"]),
            "market_total_lambda": float(selected["lambda_home"]) + float(selected["lambda_away"]),
            "market_goal_margin": float(selected["lambda_home"]) - float(selected["lambda_away"]),
        })
        result["interpretation"] = classify_team_goal_market_deviation(result, self._calibration(str(historical["competition_id"]))) if "competition_id" in historical else classify_team_goal_market_deviation(result)
        result.update({
            "market_companies": companies,
            "market_aggregation": "SINGLE_COMPANY_OVERRIDE" if company is not None else "CORRELATED_MARKET_CLUSTER_LOG_RATE_CENTER",
            "research_only": True,
        })
        return result
