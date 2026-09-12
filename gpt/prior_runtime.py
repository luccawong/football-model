"""Runtime resolver for MODEL_1 Titan historical priors.

Supports both the legacy dense-covariance store and the compact sparse-precision
store produced after the 2026-09-12 full raw-SQLite validation.  The compact
format stores the penalised-posterior precision matrix and solves only the two
fixture log-rate directions needed by Stage14, avoiding huge dense covariance
files.  Train-only process covariance is added after Laplace propagation.

No market/current-context field is admitted here.  Formal Stage14 still requires
an ACTIVE competition; SHADOW/DISABLED/INSUFFICIENT_HISTORY cannot silently
become priors.
"""
from __future__ import annotations

import json
from math import exp
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from gpt.prior_engine import (
    FORBIDDEN_PRIOR_KEYS,
    PriorEngineError,
    _season_start,
    _utc_naive,
)
from gpt.prior_competition import resolve_prior as _resolve_legacy_prior

KNOWN_ACTIVATIONS = {"ACTIVE", "SHADOW", "DISABLED", "INSUFFICIENT_HISTORY"}


def _load_store(value: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return json.loads(Path(value).read_text(encoding="utf-8"))


def _validated_context(context: Mapping[str, Any]) -> tuple[str, int]:
    competition = context.get("competition") or context.get("league")
    if not competition:
        raise PriorEngineError("Prior context missing: competition/league")
    if context.get("competition") and context.get("league") and str(context["competition"]) != str(context["league"]):
        raise PriorEngineError("Conflicting competition and league in prior context.")
    for key in context:
        lower = str(key).lower()
        if any(token in lower for token in FORBIDDEN_PRIOR_KEYS):
            raise PriorEngineError(f"Forbidden market/context key in prior context: {key}")
    for key in ("season", "home_team", "away_team"):
        if not context.get(key):
            raise PriorEngineError(f"Prior context missing: {key}")
    return str(competition), _season_start(context["season"])


def _state_reference(model: Mapping[str, Any], state_map: Mapping[tuple[str, int], int], team: str, season_start: int) -> dict[str, Any]:
    hyper = model["hyperparameters"]
    current = state_map.get((team, season_start))
    if current is not None:
        return {"state_index": current, "innovation_variance": 0.0, "fallback": "CURRENT_SEASON"}
    previous = state_map.get((team, season_start - 1))
    if previous is not None:
        return {
            "state_index": previous,
            "innovation_variance": float(hyper["transition_sd"]) ** 2,
            "fallback": "PREVIOUS_SEASON_SHRINKAGE",
        }
    return {
        "state_index": None,
        "innovation_variance": float(hyper["team_sd"]) ** 2,
        "fallback": "COMPETITION_BASELINE_NEW_TEAM",
    }


def _pd2(cov: np.ndarray) -> tuple[np.ndarray, float]:
    cov = (np.asarray(cov, dtype=float) + np.asarray(cov, dtype=float).T) / 2.0
    if cov.shape != (2, 2) or not np.all(np.isfinite(cov)):
        raise PriorEngineError("Propagated log-lambda covariance is invalid.")
    eig = np.linalg.eigvalsh(cov)
    scale = max(1.0, float(np.trace(cov)))
    target = np.finfo(float).eps * scale * 64.0
    jitter = max(0.0, target - float(np.min(eig)))
    if jitter:
        cov = cov + np.eye(2) * jitter
    if float(np.min(np.linalg.eigvalsh(cov))) <= 0.0:
        raise PriorEngineError("Could not obtain positive-definite log-lambda covariance.")
    return cov, jitter


def _resolve_compact(
    context: Mapping[str, Any],
    store: Mapping[str, Any],
    *,
    require_active: bool,
) -> dict[str, Any]:
    competition, target_season = _validated_context(context)
    status = store.get("competition_status", {}).get(competition, {})
    activation = str(status.get("activation", "SHADOW"))
    if activation not in KNOWN_ACTIVATIONS:
        raise PriorEngineError(f"Unknown prior activation for {competition}: {activation}")
    if require_active and activation != "ACTIVE":
        raise PriorEngineError(f"Competition prior is not formally active: {competition} ({activation})")

    models = store.get("competition_models") or {}
    model = models.get(competition)
    if not isinstance(model, Mapping):
        raise PriorEngineError(f"No calibrated Titan prior model for competition: {competition}")
    precision = model.get("precision_csc")
    if not isinstance(precision, Mapping):
        raise PriorEngineError(f"Compact prior model missing precision matrix: {competition}")

    theta = np.asarray(model["theta"], dtype=float)
    layout = model["parameter_layout"]
    n = int(layout["state_count"])
    ao = int(layout["attack_offset"])
    do = int(layout["defence_offset"])
    if do != ao + n:
        raise PriorEngineError("Stored compact parameter layout is inconsistent.")
    state_map = {
        (str(item["team"]), int(item["season_start"])): i
        for i, item in enumerate(model["states"])
    }
    hr = _state_reference(model, state_map, str(context["home_team"]), target_season)
    ar = _state_reference(model, state_map, str(context["away_team"]), target_season)

    xh = np.zeros(len(theta), dtype=float)
    xa = np.zeros(len(theta), dtype=float)
    xh[int(layout["mu_league"])] = 1.0
    xh[int(layout["hfa_league"])] = 1.0
    xa[int(layout["mu_league"])] = 1.0
    if hr["state_index"] is not None:
        xh[ao + int(hr["state_index"])] += 1.0
        xa[do + int(hr["state_index"])] -= 1.0
    if ar["state_index"] is not None:
        xa[ao + int(ar["state_index"])] += 1.0
        xh[do + int(ar["state_index"])] -= 1.0

    Xtarget = np.vstack([xh, xa])
    mean = Xtarget @ theta
    shape = tuple(int(x) for x in precision["shape"])
    H = sparse.csc_matrix(
        (
            np.asarray(precision["data"], dtype=float),
            np.asarray(precision["indices"], dtype=np.int32),
            np.asarray(precision["indptr"], dtype=np.int32),
        ),
        shape=shape,
    )
    if shape != (len(theta), len(theta)):
        raise PriorEngineError("Compact precision shape does not match theta.")
    try:
        solved = splu(H).solve(Xtarget.T)
    except Exception as exc:
        raise PriorEngineError(f"Compact prior precision solve failed for {competition}.") from exc
    cov = Xtarget @ solved
    innovation = float(hr["innovation_variance"]) + float(ar["innovation_variance"])
    cov[0, 0] += innovation
    cov[1, 1] += innovation

    process_cov = np.asarray(model.get("process_cov_log_lambda", np.zeros((2, 2))), dtype=float)
    if process_cov.shape != (2, 2) or not np.all(np.isfinite(process_cov)):
        raise PriorEngineError(f"Invalid train-only process covariance for {competition}.")
    cov += process_cov
    cov, jitter = _pd2(cov)

    def state_value(ref: Mapping[str, Any], offset: int) -> float:
        idx = ref["state_index"]
        return 0.0 if idx is None else float(theta[offset + int(idx)])

    mu = float(theta[int(layout["mu_league"])] )
    hfa = float(theta[int(layout["hfa_league"])] )
    packet = {
        "status": "VALID",
        "engine_version": "MODEL_1-TITAN-PRIOR-RUNTIME-2.1.0",
        "mean_log_lambda": [float(mean[0]), float(mean[1])],
        "cov_log_lambda": cov.tolist(),
        "mean_lambda": [float(exp(mean[0])), float(exp(mean[1]))],
        "source_groups": ["TEAM_DATA"],
        "calibration_ref": store.get("calibration_ref"),
        "activation": activation,
        "components": {
            "mu_league": mu,
            "mu_competition": mu,
            "hfa_league": hfa,
            "hfa_competition": hfa,
            "attack_home": state_value(hr, ao),
            "defense_home": state_value(hr, do),
            "attack_away": state_value(ar, ao),
            "defense_away": state_value(ar, do),
            "x_beta_home": 0.0,
            "x_beta_away": 0.0,
        },
        "fixture": {
            "competition": competition,
            "league": competition,
            "home_team": str(context["home_team"]),
            "away_team": str(context["away_team"]),
            "season": str(context["season"]),
            "season_start": target_season,
            "match_date": _utc_naive(context.get("match_date") or context.get("kickoff")).isoformat(sep=" ")
            if (context.get("match_date") or context.get("kickoff")) is not None else None,
        },
        "hierarchy": {
            "home_team_fallback": hr["fallback"],
            "away_team_fallback": ar["fallback"],
            "half_life_days": float(model["hyperparameters"]["half_life_days"]),
            "team_sd": float(model["hyperparameters"]["team_sd"]),
            "transition_sd": float(model["hyperparameters"]["transition_sd"]),
            "opponent_adjusted": True,
            "partial_pooling": True,
            "competition_specific_baseline": True,
            "legacy_mu_league_semantics": "competition-specific scoring baseline",
        },
        "uncertainty": {
            "method": "LAPLACE_SPARSE_PRECISION_PROPAGATION_PLUS_TRAIN_ONLY_PROCESS_COVARIANCE",
            "process_cov_log_lambda": process_cov.tolist(),
            "numerical_pd_jitter": float(jitter),
            "fixed_score_covariance_forbidden": True,
        },
        "anti_double_counting": {
            "market_inputs_used": False,
            "external_draw_label_used": False,
            "context_inputs_used": False,
            "process_covariance_train_only": True,
        },
    }
    return packet


def resolve_prior(
    context: Mapping[str, Any],
    store: Mapping[str, Any] | str | Path,
    *,
    require_active: bool = True,
) -> dict[str, Any]:
    """Resolve a formal or research Titan prior from dense or compact stores."""
    loaded = _load_store(store)
    models = loaded.get("competition_models")
    competition = context.get("competition") or context.get("league")
    model = models.get(str(competition)) if isinstance(models, Mapping) and competition else None
    if isinstance(model, Mapping) and isinstance(model.get("precision_csc"), Mapping):
        return _resolve_compact(context, loaded, require_active=require_active)
    return _resolve_legacy_prior(context, loaded, require_active=require_active)
