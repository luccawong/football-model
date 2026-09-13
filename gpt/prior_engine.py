"""MODEL_1 Titan historical Bayesian prior engine.

This module is intentionally market-blind.  The only admissible inputs to the
base prior are historical Titan match results, league identity, season, teams,
home venue, time and the hyperparameters selected by time-ordered validation.
No current bookmaker price, AH/OU/1X2 snapshot, external draw label, lineup or
narrative context is consumed here.

The latent model is a hierarchical, time-decayed Poisson attack/defence model
with team-season states.  Consecutive seasons are connected by Gaussian state
transitions, so a small current-season sample shrinks first toward the previous
season and ultimately toward the league baseline.  New/promoted teams with no
same-league predecessor shrink to the league baseline.

Uncertainty is a Laplace approximation from the fitted penalised Poisson
posterior.  The 2x2 log-lambda covariance is obtained by propagating the full
parameter covariance to the requested fixture; it is never a fixed template.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import exp, isfinite, log
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from scipy import sparse
from scipy.special import gammaln

PRIOR_ENGINE_VERSION = "MODEL_1-TITAN-PRIOR-1.0.0"
STORE_VERSION = "MODEL_1-TITAN-PRIOR-STORE-1.0.0"

# Canonical names are on the left.  Alternatives are accepted only when a real
# column with that name exists; absent fields are never synthesised.
MATCH_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "match_id": ("match_id", "id"),
    "match_date": ("kickoff", "match_date", "match_time", "date"),
    "league": ("competition", "league", "competition_name"),
    "season": ("season",),
    "home_team": ("home_team", "home_name"),
    "away_team": ("away_team", "away_name"),
    "home_score": ("home_score",),
    "away_score": ("away_score",),
}
REQUIRED_MATCH_FIELDS = tuple(MATCH_FIELD_ALIASES)
FORBIDDEN_PRIOR_KEYS = {
    "pinnacle", "bet365", "macau", "1x2", "ah", "ou", "odds",
    "draw_exclusion", "external_draw", "market_lambda", "reconstruction",
}


class PriorEngineError(ValueError):
    pass


@dataclass(frozen=True)
class HyperParameters:
    half_life_days: float
    team_sd: float
    transition_sd: float

    def validate(self) -> None:
        values = (self.half_life_days, self.team_sd, self.transition_sd)
        if not all(isfinite(float(x)) and float(x) > 0 for x in values):
            raise PriorEngineError("Prior hyperparameters must be finite and > 0.")

    def as_dict(self) -> dict[str, float]:
        self.validate()
        return {
            "half_life_days": float(self.half_life_days),
            "team_sd": float(self.team_sd),
            "transition_sd": float(self.transition_sd),
        }


def _utc_naive(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            raise PriorEngineError("match_date/kickoff is empty.")
        text = text.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            dt = None
            for fmt in (
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
            ):
                try:
                    dt = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                raise PriorEngineError(f"Unsupported match date: {value!r}")
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _season_start(value: Any) -> int:
    text = str(value).strip()
    for token in ("/", "-", "_", " "):
        text = text.replace(token, " ")
    for part in text.split():
        if len(part) == 4 and part.isdigit() and 1900 <= int(part) <= 2200:
            return int(part)
    if len(text) >= 4 and text[:4].isdigit():
        year = int(text[:4])
        if 1900 <= year <= 2200:
            return year
    raise PriorEngineError(f"Cannot parse season without inventing it: {value!r}")


def _canonical_map(columns: Sequence[str]) -> dict[str, str]:
    actual = {str(c).lower(): str(c) for c in columns}
    out: dict[str, str] = {}
    for canonical, aliases in MATCH_FIELD_ALIASES.items():
        for alias in aliases:
            if alias.lower() in actual:
                out[canonical] = actual[alias.lower()]
                break
    return out


def audit_titan_sqlite(db_path: str | Path) -> dict[str, Any]:
    """Audit the actual SQLite schema; never infer absent fields."""
    path = Path(db_path)
    if not path.exists():
        return {"status": "INVALID", "reason": "DATABASE_NOT_FOUND", "path": str(path)}
    con = sqlite3.connect(str(path))
    try:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if "matches" not in tables:
            return {
                "status": "INVALID", "reason": "MATCHES_TABLE_MISSING",
                "path": str(path), "tables": tables,
            }
        columns = [r[1] for r in con.execute("PRAGMA table_info(matches)")]
        mapping = _canonical_map(columns)
        missing = [name for name in REQUIRED_MATCH_FIELDS if name not in mapping]
        row_count = int(con.execute("SELECT COUNT(*) FROM matches").fetchone()[0])
        null_counts: dict[str, int] = {}
        for name, col in mapping.items():
            quoted = '"' + col.replace('"', '""') + '"'
            null_counts[name] = int(
                con.execute(f"SELECT COUNT(*) FROM matches WHERE {quoted} IS NULL").fetchone()[0]
            )
        date_range = None
        if "match_date" in mapping:
            col = '"' + mapping["match_date"].replace('"', '""') + '"'
            date_range = con.execute(f"SELECT MIN({col}), MAX({col}) FROM matches").fetchone()
        return {
            "status": "VALID" if not missing else "INVALID",
            "reason": None if not missing else "MISSING_REQUIRED_FIELDS",
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "tables": tables,
            "matches_columns": columns,
            "field_mapping": mapping,
            "missing_required_fields": missing,
            "matches_count": row_count,
            "null_counts": null_counts,
            "date_min_raw": date_range[0] if date_range else None,
            "date_max_raw": date_range[1] if date_range else None,
        }
    finally:
        con.close()


def load_titan_matches(db_path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    audit = audit_titan_sqlite(db_path)
    if audit.get("status") != "VALID":
        raise PriorEngineError(f"Titan database audit failed: {audit}")
    mapping: Mapping[str, str] = audit["field_mapping"]
    select = ", ".join(
        f'"{mapping[name].replace(chr(34), chr(34)*2)}" AS "{name}"'
        for name in REQUIRED_MATCH_FIELDS
    )
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        raw_rows = con.execute(f"SELECT {select} FROM matches").fetchall()
    finally:
        con.close()

    rows: list[dict[str, Any]] = []
    invalid = 0
    for raw in raw_rows:
        try:
            item = dict(raw)
            if any(item[name] is None for name in REQUIRED_MATCH_FIELDS):
                invalid += 1
                continue
            dt = _utc_naive(item["match_date"])
            season_start = _season_start(item["season"])
            hg = int(item["home_score"])
            ag = int(item["away_score"])
            if hg < 0 or ag < 0:
                invalid += 1
                continue
            rows.append({
                "match_id": str(item["match_id"]),
                "match_date": dt,
                "league": str(item["league"]).strip(),
                "season": str(item["season"]).strip(),
                "season_start": season_start,
                "home_team": str(item["home_team"]).strip(),
                "away_team": str(item["away_team"]).strip(),
                "home_score": hg,
                "away_score": ag,
            })
        except (TypeError, ValueError, PriorEngineError):
            invalid += 1
    rows.sort(key=lambda r: (r["match_date"], r["match_id"]))
    audit = dict(audit)
    audit["usable_completed_matches"] = len(rows)
    audit["excluded_invalid_matches"] = invalid
    if rows:
        audit["usable_date_min"] = rows[0]["match_date"].isoformat(sep=" ")
        audit["usable_date_max"] = rows[-1]["match_date"].isoformat(sep=" ")
        audit["leagues"] = sorted({r["league"] for r in rows})
        audit["seasons"] = sorted({r["season"] for r in rows}, key=_season_start)
    return rows, audit


def _time_weight(match_date: datetime, as_of: datetime, half_life_days: float) -> float:
    age = max(0.0, (as_of - match_date).total_seconds() / 86400.0)
    return 0.5 ** (age / float(half_life_days))


def _states(rows: Sequence[Mapping[str, Any]]) -> list[tuple[str, int]]:
    return sorted(
        {(str(r["home_team"]), int(r["season_start"])) for r in rows}
        | {(str(r["away_team"]), int(r["season_start"])) for r in rows},
        key=lambda x: (x[0], x[1]),
    )


def _add_difference_precision(P: np.ndarray, i: int, j: int, q: float) -> None:
    P[i, i] += q
    P[j, j] += q
    P[i, j] -= q
    P[j, i] -= q


def fit_league_model(
    rows: Sequence[Mapping[str, Any]],
    *,
    league: str,
    as_of: str | datetime,
    hyperparameters: HyperParameters,
    min_matches: int = 80,
    max_iter: int = 80,
    tol: float = 1e-8,
    include_precision_csc: bool = False,
) -> dict[str, Any]:
    """Fit one league using only matches strictly before ``as_of``."""
    hyperparameters.validate()
    cutoff = _utc_naive(as_of)
    data = [r for r in rows if r["league"] == league and r["match_date"] < cutoff]
    if len(data) < int(min_matches):
        raise PriorEngineError(
            f"Insufficient pre-cutoff history for {league}: {len(data)} < {min_matches}."
        )
    states = _states(data)
    n = len(states)
    state_index = {state: i for i, state in enumerate(states)}
    p = 2 + 2 * n
    attack_offset = 2
    defence_offset = 2 + n

    X = np.zeros((2 * len(data), p), dtype=float)
    y = np.zeros(2 * len(data), dtype=float)
    w = np.zeros(2 * len(data), dtype=float)
    state_effective = np.zeros(n, dtype=float)
    for k, r in enumerate(data):
        hs = (str(r["home_team"]), int(r["season_start"]))
        as_ = (str(r["away_team"]), int(r["season_start"]))
        hi = state_index[hs]
        ai = state_index[as_]
        wt = _time_weight(r["match_date"], cutoff, hyperparameters.half_life_days)
        state_effective[hi] += wt
        state_effective[ai] += wt

        rh = 2 * k
        ra = rh + 1
        X[rh, 0] = 1.0
        X[rh, 1] = 1.0
        X[rh, attack_offset + hi] = 1.0
        X[rh, defence_offset + ai] = -1.0
        y[rh] = float(r["home_score"])
        w[rh] = wt

        X[ra, 0] = 1.0
        X[ra, attack_offset + ai] = 1.0
        X[ra, defence_offset + hi] = -1.0
        y[ra] = float(r["away_score"])
        w[ra] = wt

    # Gaussian hierarchy.  Root team-season states shrink to league mean (zero).
    # Consecutive states shrink to the same team's previous season.
    P = np.zeros((p, p), dtype=float)
    P[0, 0] = 1e-8  # numerical ridge only; not a claimed empirical prior
    P[1, 1] = 1e-8
    root_q = 1.0 / (hyperparameters.team_sd ** 2)
    transition_q = 1.0 / (hyperparameters.transition_sd ** 2)
    by_team: dict[str, list[tuple[int, int]]] = {}
    for idx, (team, season_start) in enumerate(states):
        by_team.setdefault(team, []).append((season_start, idx))
    for team_states in by_team.values():
        team_states.sort()
        prev: tuple[int, int] | None = None
        for season_start, idx in team_states:
            ai = attack_offset + idx
            di = defence_offset + idx
            if prev is not None and season_start == prev[0] + 1:
                pai = attack_offset + prev[1]
                pdi = defence_offset + prev[1]
                _add_difference_precision(P, ai, pai, transition_q)
                _add_difference_precision(P, di, pdi, transition_q)
            else:
                P[ai, ai] += root_q
                P[di, di] += root_q
            prev = (season_start, idx)

    # Stable empirical initialisation for the league baseline/HFA.
    home_mean = max(1e-3, float(np.average(y[0::2], weights=w[0::2])))
    away_mean = max(1e-3, float(np.average(y[1::2], weights=w[1::2])))
    theta = np.zeros(p, dtype=float)
    theta[0] = log(away_mean)
    theta[1] = log(home_mean / away_mean)

    def objective(v: np.ndarray) -> float:
        eta = np.clip(X @ v, -10.0, 6.0)
        rate = np.exp(eta)
        return float(np.sum(w * (rate - y * eta)) + 0.5 * v @ P @ v)

    converged = False
    final_hessian = None
    for iteration in range(int(max_iter)):
        eta = np.clip(X @ theta, -10.0, 6.0)
        rate = np.exp(eta)
        grad = X.T @ (w * (rate - y)) + P @ theta
        wr = w * rate
        hessian = X.T @ (X * wr[:, None]) + P
        hessian = (hessian + hessian.T) / 2.0
        try:
            step = np.linalg.solve(hessian, grad)
        except np.linalg.LinAlgError as exc:
            raise PriorEngineError(f"Prior Hessian solve failed for {league}.") from exc
        old = objective(theta)
        alpha = 1.0
        accepted = False
        for _ in range(20):
            candidate = theta - alpha * step
            new = objective(candidate)
            if np.isfinite(new) and new <= old:
                theta = candidate
                accepted = True
                break
            alpha *= 0.5
        if not accepted:
            raise PriorEngineError(f"Prior optimiser line search failed for {league}.")
        final_hessian = hessian
        if float(np.max(np.abs(alpha * step))) < float(tol):
            converged = True
            break

    # Recompute Hessian exactly at the final mode before covariance extraction.
    eta = np.clip(X @ theta, -10.0, 6.0)
    rate = np.exp(eta)
    final_hessian = X.T @ (X * (w * rate)[:, None]) + P
    final_hessian = (final_hessian + final_hessian.T) / 2.0
    try:
        covariance = np.linalg.inv(final_hessian)
    except np.linalg.LinAlgError as exc:
        raise PriorEngineError(f"Prior covariance inversion failed for {league}.") from exc
    covariance = (covariance + covariance.T) / 2.0
    eig = np.linalg.eigvalsh(covariance)
    if float(np.min(eig)) <= 0.0:
        raise PriorEngineError(f"Non-positive parameter covariance for {league}.")

    result = {
        "engine_version": PRIOR_ENGINE_VERSION,
        "status": "FITTED",
        "league": league,
        "as_of": cutoff.isoformat(sep=" "),
        "hyperparameters": hyperparameters.as_dict(),
        "n_matches": len(data),
        "n_states": n,
        "effective_match_weight": float(np.sum(w[0::2])),
        "converged": converged,
        "iterations": iteration + 1,
        "states": [
            {
                "team": team,
                "season_start": season_start,
                "effective_matches": float(state_effective[idx]),
            }
            for idx, (team, season_start) in enumerate(states)
        ],
        "theta": theta.tolist(),
        "covariance": covariance.tolist(),
        "parameter_layout": {
            "mu_league": 0,
            "hfa_league": 1,
            "attack_offset": attack_offset,
            "defence_offset": defence_offset,
            "state_count": n,
        },
        "objective": objective(theta),
    }
    if include_precision_csc:
        precision = sparse.csc_matrix(final_hessian)
        result["precision_csc"] = {
            "data": precision.data.tolist(),
            "indices": precision.indices.tolist(),
            "indptr": precision.indptr.tolist(),
            "shape": list(precision.shape),
        }
    return result


def _model_arrays(model: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray, dict[tuple[str, int], int]]:
    theta = np.asarray(model["theta"], dtype=float)
    covariance = np.asarray(model["covariance"], dtype=float)
    if covariance.shape != (len(theta), len(theta)):
        raise PriorEngineError("Stored parameter covariance has invalid shape.")
    state_map = {
        (str(s["team"]), int(s["season_start"])): i
        for i, s in enumerate(model["states"])
    }
    return theta, covariance, state_map


def _state_reference(
    model: Mapping[str, Any],
    state_map: Mapping[tuple[str, int], int],
    team: str,
    target_season: int,
) -> dict[str, Any]:
    hyper = model["hyperparameters"]
    current = state_map.get((team, target_season))
    if current is not None:
        return {"state_index": current, "innovation_variance": 0.0, "fallback": "CURRENT_SEASON"}
    previous = state_map.get((team, target_season - 1))
    if previous is not None:
        return {
            "state_index": previous,
            "innovation_variance": float(hyper["transition_sd"]) ** 2,
            "fallback": "PREVIOUS_SEASON_SHRINKAGE",
        }
    return {
        "state_index": None,
        "innovation_variance": float(hyper["team_sd"]) ** 2,
        "fallback": "LEAGUE_BASELINE_NEW_OR_PROMOTED_TEAM",
    }


def _positive_definite_2x2(cov: np.ndarray) -> tuple[np.ndarray, float]:
    cov = (np.asarray(cov, dtype=float) + np.asarray(cov, dtype=float).T) / 2.0
    if cov.shape != (2, 2) or not np.all(np.isfinite(cov)):
        raise PriorEngineError("Propagated log-lambda covariance is invalid.")
    eig = np.linalg.eigvalsh(cov)
    scale = max(1.0, float(np.trace(cov)))
    target = np.finfo(float).eps * scale * 64.0
    jitter = max(0.0, target - float(np.min(eig)))
    if jitter > 0:
        cov = cov + np.eye(2) * jitter
    if float(np.min(np.linalg.eigvalsh(cov))) <= 0.0:
        raise PriorEngineError("Could not obtain positive-definite log-lambda covariance.")
    return cov, jitter


def build_prior_packet_from_model(
    model: Mapping[str, Any],
    *,
    home_team: str,
    away_team: str,
    season: str | int,
    match_date: str | datetime | None = None,
    calibration_ref: str | None = None,
) -> dict[str, Any]:
    """Propagate one fitted historical league model to a fixture prior packet."""
    if any(k.lower() in FORBIDDEN_PRIOR_KEYS for k in model.keys()):
        raise PriorEngineError("Prior model contains a forbidden market-derived top-level key.")
    if match_date is not None and model.get("as_of") is not None:
        if _utc_naive(model["as_of"]) > _utc_naive(match_date):
            raise PriorEngineError("Prior model state is later than the requested fixture.")
    target_season = _season_start(season)
    theta, parameter_cov, state_map = _model_arrays(model)
    layout = model["parameter_layout"]
    n = int(layout["state_count"])
    ao = int(layout["attack_offset"])
    do = int(layout["defence_offset"])
    if do != ao + n:
        raise PriorEngineError("Stored parameter layout is inconsistent.")

    hr = _state_reference(model, state_map, str(home_team), target_season)
    ar = _state_reference(model, state_map, str(away_team), target_season)
    xh = np.zeros(len(theta), dtype=float)
    xa = np.zeros(len(theta), dtype=float)
    xh[int(layout["mu_league"])] = 1.0
    xh[int(layout["hfa_league"])] = 1.0
    xa[int(layout["mu_league"])] = 1.0

    # Home lambda: home attack - away defence.
    if hr["state_index"] is not None:
        xh[ao + int(hr["state_index"])] += 1.0
    if ar["state_index"] is not None:
        xh[do + int(ar["state_index"])] -= 1.0
    # Away lambda: away attack - home defence.
    if ar["state_index"] is not None:
        xa[ao + int(ar["state_index"])] += 1.0
    if hr["state_index"] is not None:
        xa[do + int(hr["state_index"])] -= 1.0

    Xtarget = np.vstack([xh, xa])
    mean = Xtarget @ theta
    cov = Xtarget @ parameter_cov @ Xtarget.T
    # Innovations for an unseen target season/team are independent attack/defence
    # state innovations.  Their variance is estimated via calibrated hierarchy
    # hyperparameters, not a score-level covariance constant.
    cov[0, 0] += float(hr["innovation_variance"]) + float(ar["innovation_variance"])
    cov[1, 1] += float(ar["innovation_variance"]) + float(hr["innovation_variance"])
    cov, jitter = _positive_definite_2x2(cov)

    def state_value(ref: Mapping[str, Any], offset: int) -> float:
        idx = ref["state_index"]
        return 0.0 if idx is None else float(theta[offset + int(idx)])

    packet = {
        "status": "VALID",
        "engine_version": PRIOR_ENGINE_VERSION,
        "mean_log_lambda": [float(mean[0]), float(mean[1])],
        "cov_log_lambda": cov.tolist(),
        "mean_lambda": [float(exp(mean[0])), float(exp(mean[1]))],
        "source_groups": ["TEAM_DATA"],
        "calibration_ref": calibration_ref,
        "state_as_of": model.get("as_of"),
        "components": {
            "mu_league": float(theta[int(layout["mu_league"])]),
            "hfa_league": float(theta[int(layout["hfa_league"])]),
            "attack_home": state_value(hr, ao),
            "defense_home": state_value(hr, do),
            "attack_away": state_value(ar, ao),
            "defense_away": state_value(ar, do),
            "x_beta_home": 0.0,
            "x_beta_away": 0.0,
        },
        "fixture": {
            "league": model["league"],
            "home_team": str(home_team),
            "away_team": str(away_team),
            "season": str(season),
            "season_start": target_season,
            "match_date": _utc_naive(match_date).isoformat(sep=" ") if match_date is not None else None,
        },
        "hierarchy": {
            "home_team_fallback": hr["fallback"],
            "away_team_fallback": ar["fallback"],
            "half_life_days": float(model["hyperparameters"]["half_life_days"]),
            "team_sd": float(model["hyperparameters"]["team_sd"]),
            "transition_sd": float(model["hyperparameters"]["transition_sd"]),
            "opponent_adjusted": True,
            "partial_pooling": True,
            "league_specific_baseline": True,
        },
        "uncertainty": {
            "method": "LAPLACE_FULL_PARAMETER_COVARIANCE_PROPAGATION",
            "numerical_pd_jitter": float(jitter),
            "fixed_score_covariance_forbidden": True,
        },
        "anti_double_counting": {
            "market_inputs_used": False,
            "external_draw_label_used": False,
            "context_inputs_used": False,
        },
    }
    return packet


def _poisson_nll(y: int, lam: float) -> float:
    if not (lam > 0 and isfinite(lam)):
        return float("inf")
    return float(lam - int(y) * log(lam) + gammaln(int(y) + 1.0))


def _season_rows(rows: Sequence[Mapping[str, Any]], league: str, season_start: int) -> list[Mapping[str, Any]]:
    return [r for r in rows if r["league"] == league and int(r["season_start"]) == int(season_start)]


def calibrate_hyperparameters(
    rows: Sequence[Mapping[str, Any]],
    *,
    league: str,
    train_seasons: Sequence[str | int],
    half_life_candidates: Sequence[float],
    team_sd_candidates: Sequence[float],
    transition_sd_candidates: Sequence[float],
    min_fold_train_seasons: int = 1,
    min_matches: int = 80,
) -> dict[str, Any]:
    """Nested season-forward hyperparameter selection using prior-only goal NLL.

    Only seasons inside ``train_seasons`` participate.  Later validation/test
    seasons therefore cannot tune half-life or shrinkage.
    """
    season_keys = sorted({_season_start(x) for x in train_seasons})
    folds: list[tuple[list[int], int]] = []
    for i in range(int(min_fold_train_seasons), len(season_keys)):
        folds.append((season_keys[:i], season_keys[i]))
    if not folds:
        return {"status": "CALIBRATION_REQUIRED", "reason": "NO_INNER_TIME_FOLD"}

    results: list[dict[str, Any]] = []
    for hl in half_life_candidates:
        for tsd in team_sd_candidates:
            for dsd in transition_sd_candidates:
                hyper = HyperParameters(float(hl), float(tsd), float(dsd))
                hyper.validate()
                losses: list[float] = []
                matches_scored = 0
                valid_candidate = True
                for train_keys, val_key in folds:
                    val_rows = _season_rows(rows, league, val_key)
                    if not val_rows:
                        continue
                    cutoff = min(r["match_date"] for r in val_rows)
                    allowed = [
                        r for r in rows
                        if r["league"] == league and int(r["season_start"]) in train_keys
                    ]
                    try:
                        model = fit_league_model(
                            allowed, league=league, as_of=cutoff,
                            hyperparameters=hyper, min_matches=min_matches,
                        )
                    except PriorEngineError:
                        valid_candidate = False
                        break
                    for r in val_rows:
                        packet = build_prior_packet_from_model(
                            model,
                            home_team=r["home_team"], away_team=r["away_team"],
                            season=r["season"], match_date=r["match_date"],
                            calibration_ref="INNER_SEASON_FORWARD",
                        )
                        lh, la = packet["mean_lambda"]
                        losses.append(_poisson_nll(r["home_score"], lh))
                        losses.append(_poisson_nll(r["away_score"], la))
                        matches_scored += 1
                if valid_candidate and losses:
                    results.append({
                        **hyper.as_dict(),
                        "mean_goal_nll": float(np.mean(losses)),
                        "matches_scored": matches_scored,
                        "folds": len(folds),
                    })
    if not results:
        return {"status": "CALIBRATION_REQUIRED", "reason": "NO_VALID_HYPERPARAMETER_CANDIDATE"}
    results.sort(key=lambda r: (r["mean_goal_nll"], -r["matches_scored"]))
    return {
        "status": "VALIDATED_ON_TRAIN_FOLDS",
        "selection_metric": "PRIOR_ONLY_GOAL_POISSON_NLL",
        "time_ordered": True,
        "selected": {
            k: results[0][k] for k in ("half_life_days", "team_sd", "transition_sd")
        },
        "leaderboard": results,
        "train_seasons": [str(x) for x in train_seasons],
    }


def build_prior_store(
    rows: Sequence[Mapping[str, Any]],
    *,
    hyperparameters_by_league: Mapping[str, Mapping[str, float]],
    as_of: str | datetime,
    dataset_audit: Mapping[str, Any] | None = None,
    calibration: Mapping[str, Any] | None = None,
    min_matches: int = 80,
) -> dict[str, Any]:
    cutoff = _utc_naive(as_of)
    models: dict[str, Any] = {}
    for league, raw_hyper in hyperparameters_by_league.items():
        hyper = HyperParameters(
            float(raw_hyper["half_life_days"]),
            float(raw_hyper["team_sd"]),
            float(raw_hyper["transition_sd"]),
        )
        models[str(league)] = fit_league_model(
            rows, league=str(league), as_of=cutoff,
            hyperparameters=hyper, min_matches=min_matches,
        )
    provenance = {
        "engine_version": PRIOR_ENGINE_VERSION,
        "dataset_matches": dataset_audit.get("matches_count") if dataset_audit else None,
        "dataset_date_min": dataset_audit.get("usable_date_min") if dataset_audit else None,
        "dataset_date_max": dataset_audit.get("usable_date_max") if dataset_audit else None,
        "as_of": cutoff.isoformat(sep=" "),
        "leagues": sorted(models),
    }
    fingerprint = sha256(
        json.dumps(provenance, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "store_version": STORE_VERSION,
        "status": "VALID",
        "created_from": "TITAN_HISTORICAL_MATCH_RESULTS_ONLY",
        "as_of": cutoff.isoformat(sep=" "),
        "dataset_audit": dict(dataset_audit or {}),
        "calibration": dict(calibration or {}),
        "calibration_ref": f"{STORE_VERSION}:{fingerprint[:16]}",
        "league_models": models,
        "forbidden_sources": ["Pinnacle", "Bet365", "Macau", "1X2", "AH", "OU", "DRAW_EXCLUSION"],
    }


def save_prior_store(store: Mapping[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def load_prior_store(value: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, Mapping):
        store = dict(value)
    else:
        store = json.loads(Path(value).read_text(encoding="utf-8"))
    if store.get("status") != "VALID" or not isinstance(store.get("league_models"), Mapping):
        raise PriorEngineError("Prior store is missing or invalid.")
    return store


def build_prior_packet(
    context: Mapping[str, Any],
    store: Mapping[str, Any] | str | Path,
) -> dict[str, Any]:
    """Resolve a formal Stage14 prior from match context + calibrated store."""
    required = ("league", "season", "home_team", "away_team")
    missing = [k for k in required if not context.get(k)]
    if missing:
        raise PriorEngineError(f"Prior context missing: {', '.join(missing)}")
    for key in context:
        lower = str(key).lower()
        if any(token in lower for token in FORBIDDEN_PRIOR_KEYS):
            raise PriorEngineError(f"Forbidden market/context key in prior context: {key}")
    loaded = load_prior_store(store)
    league = str(context["league"])
    model = loaded["league_models"].get(league)
    if not isinstance(model, Mapping):
        raise PriorEngineError(f"No calibrated Titan prior model for league: {league}")
    return build_prior_packet_from_model(
        model,
        home_team=str(context["home_team"]),
        away_team=str(context["away_team"]),
        season=context["season"],
        match_date=context.get("match_date") or context.get("kickoff"),
        calibration_ref=loaded.get("calibration_ref"),
    )
