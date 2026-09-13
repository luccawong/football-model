"""Market-blind domestic dynamic priors. All result ingestion is strictly pre-cutoff.

Monthly is a Gaussian random-walk/Laplace filter. Rolling models refit trailing
30/60/90-day evidence against the previous-season posterior (never the previous
overlapping window), avoiding double counting. Hyperparameters are external,
frozen Train selections; this module does not tune on runtime results.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Mapping

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from gpt.prior_engine import PriorEngineError, _utc_naive, _season_start

DOMESTIC = ("英超", "西甲", "意甲", "德甲", "法甲")
VERSION = "DOMESTIC-PRIOR-V2"
TRAIN_SEASONS = (2021, 2022, 2023)


@dataclass(frozen=True)
class DynamicHyper:
    structure: str = "monthly"
    half_life_days: float = 180.0
    team_sd: float = 0.35
    transition_sd: float = 0.2

    def validate(self):
        if self.structure not in ("monthly", "rolling30", "rolling60", "rolling90"):
            raise PriorEngineError("Unknown domestic state structure")
        if any(not np.isfinite(v) or v <= 0 for v in
               (self.half_life_days, self.team_sd, self.transition_sd)):
            raise PriorEngineError("Dynamic hyperparameters must be finite and positive")


def pd(matrix):
    a = np.asarray(matrix, float)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or not np.isfinite(a).all():
        raise PriorEngineError("Invalid covariance")
    a = (a + a.T) / 2
    # Numerical floor only, never an empirical covariance template.
    floor = 64 * np.finfo(float).eps * max(1., float(np.trace(a)))
    a += np.eye(len(a)) * max(0., floor - np.linalg.eigvalsh(a)[0])
    np.linalg.cholesky(a)
    return a


def inv(a):
    return cho_solve(cho_factor(pd(a), lower=True), np.eye(len(a)))


def design(teams, home, away):
    n = len(teams)
    x = np.zeros((2, 2 + 2 * n))
    x[0, :2] = 1.
    x[1, 0] = 1.
    hi, ai = teams.index(home), teams.index(away)
    x[0, 2 + hi] = x[1, 2 + ai] = 1.
    x[0, 2 + n + ai] = x[1, 2 + n + hi] = -1.
    return x


def laplace(rows, teams, mean, covariance, cutoff, half_life):
    if not rows:
        return mean.copy(), covariance.copy()
    if any(r["match_date"] >= cutoff for r in rows):
        raise PriorEngineError("Future result in dynamic fit")
    x = np.vstack([design(teams, r["home_team"], r["away_team"]) for r in rows])
    y = np.asarray([[r["home_score"], r["away_score"]] for r in rows]).ravel()
    w = np.repeat([2 ** (-(cutoff-r["match_date"]).total_seconds()/86400/half_life)
                   for r in rows], 2)
    precision = inv(covariance)
    theta = mean.copy()

    def objective(v):
        eta = x @ v
        if np.max(eta) > 30:
            return np.inf
        delta = v - mean
        return float(np.sum(w * (np.exp(eta) - y * eta)) + .5 * delta @ precision @ delta)

    for _ in range(60):
        rate = np.exp(x @ theta)
        gradient = x.T @ (w * (rate-y)) + precision @ (theta-mean)
        hessian = (x.T * (w*rate)) @ x + precision
        step = cho_solve(cho_factor(hessian, lower=True), gradient)
        old, scale = objective(theta), 1.
        while objective(theta-scale*step) > old + 1e-10 and scale > 2**-20:
            scale *= .5
        theta -= scale * step
        if np.max(np.abs(scale*step)) < 1e-7:
            break
    else:
        raise PriorEngineError("Domestic Laplace optimizer failed to converge")
    hessian = (x.T * (w*np.exp(x @ theta))) @ x + precision
    return theta, pd(cho_solve(cho_factor(hessian, lower=True), np.eye(len(theta))))


def _expand(teams, mean, cov, additions, hyper, promoted):
    new_teams = sorted(set(teams) | set(additions))
    if new_teams == teams:
        return teams, mean.copy(), cov.copy()
    n, m = len(teams), len(new_teams)
    mu = np.zeros(2+2*m)
    sigma = np.eye(2+2*m) * hyper.team_sd**2
    # Existing baseline and team uncertainty is preserved in full.
    mapping = [0, 1] + [2+new_teams.index(t) for t in teams] + [2+m+new_teams.index(t) for t in teams]
    mu[mapping] = mean
    sigma[np.ix_(mapping, mapping)] = cov
    for t in set(new_teams)-set(teams):
        i = new_teams.index(t)
        mu[[2+i, 2+m+i]] = promoted.get("mean", [0., 0.])
        if promoted.get("status") == "ESTIMATED":
            sigma[np.ix_([2+i, 2+m+i], [2+i, 2+m+i])] = promoted["covariance"]
    return new_teams, mu, pd(sigma)


def _transition(mean, cov, hyper, elapsed=1.):
    # Mean reversion toward competition baseline plus learned innovation.
    decay = 2 ** (-max(0., elapsed)*30/hyper.half_life_days)
    d = np.ones(len(mean)); d[2:] = decay
    result = cov * np.outer(d, d)
    result[2:, 2:] += np.eye(len(mean)-2) * hyper.transition_sd**2 * max(elapsed, 0.)
    return mean*d, pd(result)


def fit_dynamic(rows, competition, cutoff, hyper, promoted=None):
    """Rebuild dynamic state from completed historical results only.

    The first observed season initializes competition baseline/HFA empirically;
    predictions require at least one completed season. Promotion class parameters
    must be estimated upstream on Train, or this uses the explicit mean fallback.
    """
    hyper.validate()
    if competition not in DOMESTIC:
        raise PriorEngineError("European competitions are frozen outside Domestic V2")
    cutoff = _utc_naive(cutoff)
    data = sorted((r for r in rows if r["league"] == competition and r["match_date"] < cutoff),
                  key=lambda r: (r["match_date"], r["match_id"]))
    if len(data) < 80:
        raise PriorEngineError("INSUFFICIENT_HISTORY")
    promoted = promoted or {"status": "FALLBACK", "mean": [0., 0.]}
    seasons = sorted({r["season_start"] for r in data})
    base = [r for r in data if r["season_start"] == seasons[0]]
    teams = sorted({r[k] for r in base for k in ("home_team", "away_team")})
    n = len(teams)
    hg, ag = np.mean([[r["home_score"], r["away_score"]] for r in base], axis=0)
    mean = np.zeros(2+2*n); mean[:2] = [np.log(max(ag,.01)), np.log(max(hg,.01)/max(ag,.01))]
    # Baseline starting precision is numerical only, posterior comes from results.
    cov = np.eye(len(mean))*hyper.team_sd**2; cov[:2,:2] = np.eye(2)*1e8
    base_end = min(cutoff, max(r["match_date"] for r in base)+timedelta(seconds=1))
    mean, cov = laplace(base, teams, mean, cov, base_end, hyper.half_life_days)
    previous_teams = set(teams)
    fallback = {}
    for season in seasons[1:]:
        current = [r for r in data if r["season_start"] == season]
        current_teams = sorted({r[k] for r in current for k in ("home_team", "away_team")})
        # Teams absent in the immediately previous season are new class members,
        # even if they appeared in an older season in this competition.
        keep = [t for t in teams if t in previous_teams]
        ix = [0,1]+[2+teams.index(t) for t in keep]+[2+len(teams)+teams.index(t) for t in keep]
        mean, cov, teams = mean[ix], cov[np.ix_(ix,ix)], keep
        mean, cov = _transition(mean, cov, hyper)
        teams, mean, cov = _expand(teams, mean, cov, current_teams, hyper, promoted)
        fallback = {t: ("PREVIOUS_SEASON_TRANSITION" if t in previous_teams else
                        "PROMOTED_CLASS" if promoted.get("status") == "ESTIMATED" else
                        "COMPETITION_MEAN_PLUS_CURRENT_EVIDENCE") for t in current_teams}
        anchor_mean, anchor_cov = mean.copy(), cov.copy()
        if hyper.structure == "monthly":
            months = sorted({(r["match_date"].year, r["match_date"].month) for r in current})
            last_month = None
            for year, month in months:
                month_index = year*12+month
                if last_month is not None:
                    mean, cov = _transition(mean, cov, hyper, month_index-last_month)
                batch = [r for r in current if (r["match_date"].year,r["match_date"].month)==(year,month)]
                # Each result enters once. Rebuilds include only observed results.
                end = min(cutoff, datetime(year+int(month==12), month%12+1, 1))
                mean, cov = laplace(batch, teams, mean, cov, end, hyper.half_life_days)
                last_month = month_index
            gap = cutoff.year*12+cutoff.month-last_month
            if gap > 0 and season == seasons[-1]:
                mean, cov = _transition(mean, cov, hyper, gap)
        else:
            end = cutoff if season == seasons[-1] else max(r["match_date"] for r in current)+timedelta(seconds=1)
            window = int(hyper.structure[7:])
            recent = [r for r in current if r["match_date"] >= end-timedelta(days=window)]
            elapsed = max(1., (end-min(r["match_date"] for r in current)).days/30)
            mean, cov = _transition(anchor_mean, anchor_cov, hyper, elapsed)
            mean, cov = laplace(recent, teams, mean, cov, end, hyper.half_life_days)
        previous_teams = set(current_teams)
    return {"engine_version": VERSION, "competition": competition, "as_of": cutoff.isoformat(),
            "last_result": max(r["match_date"] for r in data).isoformat(),
            "season_start": seasons[-1], "teams": teams, "theta": mean.tolist(),
            "covariance": cov.tolist(), "hyperparameters": asdict(hyper),
            "promoted_class": promoted, "team_fallback": fallback, "n_matches": len(data)}


def dynamic_packet(model, home, away, season, kickoff, calibration=None):
    cutoff = _utc_naive(kickoff)
    if _utc_naive(model["as_of"]) > cutoff or _utc_naive(model["last_result"]) >= cutoff:
        raise PriorEngineError("Dynamic state contains future results")
    target = _season_start(season)
    if target < model["season_start"]:
        raise PriorEngineError("Dynamic state is newer than requested season")
    hyper = DynamicHyper(**model["hyperparameters"])
    teams, mean, cov = list(model["teams"]), np.array(model["theta"]), np.array(model["covariance"])
    if target > model["season_start"]:
        mean, cov = _transition(mean, cov, hyper, target-model["season_start"])
    teams, mean, cov = _expand(teams, mean, cov, [home,away], hyper, model["promoted_class"])
    x = design(teams, home, away)
    mu, lap = x @ mean, pd(x @ cov @ x.T)
    calibration = calibration or {}
    process = np.array(calibration.get("process_covariance", [[0.,0.],[0.,0.]]))
    kappa = float(calibration.get("kappa", 1.))
    if process.shape != (2,2) or not np.isfinite(process).all() or not np.allclose(process,process.T) or np.linalg.eigvalsh(process)[0] < -1e-12:
        raise PriorEngineError("Invalid process covariance")
    if not np.isfinite(kappa) or kappa <= 0:
        raise PriorEngineError("Invalid covariance inflation")
    effective = pd(kappa*(lap+process))
    return {"status": "VALID", "activation": "SHADOW", "engine_version": VERSION, "source_groups": ["TEAM_DATA"],
            "mean_log_lambda": mu.tolist(), "mean_lambda": np.exp(mu).tolist(),
            "cov_log_lambda": effective.tolist(), "calibration_ref": calibration.get("ref"),
            "rho_prior": {"mean": float(calibration.get("rho",0.)), "validated": bool(calibration),
                          "scope": "TRAIN_SEASON_FORWARD"},
            "uncertainty": {"laplace_covariance": lap.tolist(), "process_covariance": process.tolist(),
                            "kappa": kappa, "method": "LAPLACE_PLUS_TRAIN_PROCESS_TIMES_TRAIN_KAPPA"},
            "hierarchy": {"structure": hyper.structure, "opponent_adjusted": True,
                          "home_team_fallback": model["team_fallback"].get(home, "PROMOTED_CLASS" if model["promoted_class"]["status"]=="ESTIMATED" else "COMPETITION_MEAN_PLUS_CURRENT_EVIDENCE"),
                          "away_team_fallback": model["team_fallback"].get(away, "PROMOTED_CLASS" if model["promoted_class"]["status"]=="ESTIMATED" else "COMPETITION_MEAN_PLUS_CURRENT_EVIDENCE")},
            "anti_double_counting": {"market_inputs_used": False, "external_draw_label_used": False},
            "fixture": {"competition": model["competition"], "season": season, "home_team": home,
                        "away_team": away, "match_date": cutoff.isoformat()}}
