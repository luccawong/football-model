from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from gpt.prior_engine import PriorEngineError
from gpt.prior_runtime import resolve_prior
from gpt.quant_core import score_grid, correct_score_probabilities
from gpt.stage14_bayesian import (
    _ou_references,
    build_formal_market_score_packet,
    build_market_cluster_likelihood,
    build_stage14_score_packet,
)

SCORE_ENGINE_MODES = {"AUTO", "HISTORICAL_BAYESIAN", "MARKET_ONLY_FORMAL"}
FORBIDDEN_USEFULNESS_KEYS = {
    "actual_score", "actual_result", "home_score", "away_score", "final_score",
    "post_match_result", "future_matches", "test_target", "jcb_result", "post_kickoff",
}


def market_reconstruction_top3(quant_packet: Mapping[str, Any], company: str) -> dict[str, Any]:
    """Legacy/research-only market reconstruction view.

    This is never the formal MODEL_1 Stage14 output after the Bayesian engine repair.
    """
    reconstruction = quant_packet.get("reconstruction", {})
    if company not in reconstruction:
        return {"status": "MISSING", "reason": "NO_RECONSTRUCTION", "top3": []}
    rec = reconstruction[company]
    grid = score_grid(float(rec["lambda_home"]), float(rec["lambda_away"]), float(rec["rho"]))
    rows = correct_score_probabilities(grid, 10)
    return {
        "status": "MARKET_RECONSTRUCTION_RESEARCH_ONLY",
        "top3": rows[:3],
        "top10": rows,
        "formal_stage14": False,
    }


def _formal_execution_path(execution_path: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    """Enforce MODEL_1's formal AH scoreline gate on Stage14 output.

    If a formal AH path is supplied, every displayed scoreline must settle the
    selected AH side positively. The posterior distribution itself remains
    untouched; only final scoreline eligibility is filtered.
    """
    if execution_path is None:
        return None
    path = dict(execution_path)
    ah = path.get("ah")
    if isinstance(ah, Mapping):
        ah_path = dict(ah)
        if bool(ah_path.get("formal", True)):
            ah_path["hard_gate"] = True
            ah_path["positive_settlement_required"] = True
            ah_path["push_allowed"] = False
        path["ah"] = ah_path
    return path


def automatic_top3(
    quant_packet: Mapping[str, Any],
    company: str | None = None,
    *,
    prior_packet: Mapping[str, Any] | None = None,
    prior_context: Mapping[str, Any] | None = None,
    prior_store: Mapping[str, Any] | str | Path | None = None,
    context_updates: Sequence[Mapping[str, Any]] | None = None,
    execution_path: Mapping[str, Any] | None = None,
    market_absorbed_fraction: float = 0.0,
    market_sigma_floor: float = 0.12,
    max_goals: int = 12,
    draws: int = 4000,
) -> dict[str, Any]:
    """Formal MODEL_1 automatic Stage14 entry point.

    A validated Bayesian prior is mandatory. Callers may still pass a pre-built
    ``prior_packet``. Alternatively ``prior_context`` + a calibrated Titan
    ``prior_store`` resolve the packet automatically. The preferred metadata key
    is ``competition``; legacy ``league`` remains accepted. The resolver admits
    only competitions whose OOS activation is ACTIVE. SHADOW, DISABLED and
    INSUFFICIENT_HISTORY cannot silently become formal priors.

    ``company`` is accepted only for backward call compatibility and is not used
    to select a single bookmaker for the formal posterior. Pinnacle/Bet365/Macau
    are fused later as one correlated market likelihood cluster.
    """
    resolution = "EXPLICIT_PRIOR_PACKET"
    if prior_packet is None and prior_store is not None:
        context = prior_context
        if context is None:
            embedded = quant_packet.get("prior_context") or quant_packet.get("match_context")
            context = embedded if isinstance(embedded, Mapping) else None
        if context is None:
            return {
                "status": "MISSING",
                "reason": "BAYESIAN_PRIOR_CONTEXT_REQUIRED",
                "top3": [],
                "no_market_only_fallback": True,
            }
        try:
            prior_packet = resolve_prior(context, prior_store, require_active=True)
            resolution = "AUTO_TITAN_HISTORICAL_PRIOR"
        except PriorEngineError as exc:
            return {
                "status": "MISSING",
                "reason": "BAYESIAN_PRIOR_UNAVAILABLE",
                "detail": str(exc),
                "top3": [],
                "no_market_only_fallback": True,
            }

    if prior_packet is None:
        return {
            "status": "MISSING",
            "reason": "BAYESIAN_PRIOR_REQUIRED",
            "top3": [],
            "no_market_only_fallback": True,
        }
    out = build_stage14_score_packet(
        quant_packet,
        prior_packet,
        context_updates=context_updates,
        execution_path=_formal_execution_path(execution_path),
        market_absorbed_fraction=market_absorbed_fraction,
        market_sigma_floor=market_sigma_floor,
        max_goals=max_goals,
        draws=draws,
    )
    out["prior_resolution"] = resolution
    return out


def _read_store(value: Mapping[str, Any] | str | Path | None) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if value is None:
        return {}
    return __import__("json").loads(Path(value).read_text(encoding="utf-8"))


def _activation(store: Mapping[str, Any] | str | Path | None, competition: str) -> str:
    payload = _read_store(store)
    raw = payload.get("competition_status", {}).get(competition, {})
    return str(raw.get("activation", "UNAVAILABLE")) if isinstance(raw, Mapping) else "UNAVAILABLE"


def _snapshot_phase(explicit: str | None, quant_packet: Mapping[str, Any]) -> str:
    candidates = [explicit, quant_packet.get("snapshot_phase")]
    for key in ("market_snapshot", "snapshot_metadata", "metadata"):
        value = quant_packet.get(key)
        if isinstance(value, Mapping):
            candidates.extend((value.get("snapshot_phase"), value.get("phase")))
    for value in candidates:
        if value is not None:
            phase = str(value).strip().lower()
            if phase in {"opening", "closing", "current"}:
                return phase
            raise ValueError("snapshot_phase must be opening, closing, or current")
    return "current"


def _forbidden_runtime_key(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            matched = next(
                (token for token in FORBIDDEN_USEFULNESS_KEYS if token in normalized), None
            )
            if matched:
                return matched
            found = _forbidden_runtime_key(child)
            if found:
                return found
    elif isinstance(value, (list, tuple)):
        for child in value:
            found = _forbidden_runtime_key(child)
            if found:
                return found
    return None


def prior_usefulness_gate(
    *,
    quant_packet: Mapping[str, Any],
    historical_prior_activation: str,
    prior_packet: Mapping[str, Any] | None,
    snapshot_phase: str,
    runtime_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Conservative production gate using pre-kickoff features only.

    No stable Train-only domestic subset was approved by Domestic Prior V2, so
    the first production rule admits the prior only when its competition-level
    activation is ACTIVE. Candidate features are emitted for future Train-only
    research; they do not use or inspect a realized score.
    """
    metadata = dict(runtime_metadata or {})
    forbidden = _forbidden_runtime_key(quant_packet) or _forbidden_runtime_key(metadata)
    if forbidden:
        raise ValueError(f"Post-result field is forbidden in prior usefulness gate: {forbidden}")
    market = build_market_cluster_likelihood(quant_packet)
    observations = list(market.get("company_observations", []))
    lambdas = np.asarray(
        [[row["lambda_home"], row["lambda_away"]] for row in observations], dtype=float
    ) if observations else np.empty((0, 2))
    prior_cov = np.asarray(prior_packet.get("cov_log_lambda"), dtype=float) if prior_packet else None
    market_cov = np.asarray(market.get("cov_log_lambda"), dtype=float) if market.get("status") == "VALID" else None
    distance = None
    if prior_packet and market.get("status") == "VALID":
        distance = float(np.linalg.norm(
            np.asarray(prior_packet["mean_log_lambda"], dtype=float)
            - np.asarray(market["mean_log_lambda"], dtype=float)
        ))
    features = {
        "market_cluster_covariance": market_cov.tolist() if market_cov is not None else None,
        "core_market_lambda_dispersion": (
            np.std(lambdas, axis=0, ddof=1).tolist() if len(lambdas) >= 2 else [0.0, 0.0] if len(lambdas) else None
        ),
        "market_reconstruction_residual": market.get("fit_residual_mean"),
        "snapshot_phase": snapshot_phase,
        "season_progress": metadata.get("season_progress"),
        "promoted_or_new_team": metadata.get("promoted_or_new_team"),
        "historical_prior_covariance": prior_cov.tolist() if prior_cov is not None else None,
        "historical_market_log_lambda_distance": distance,
        "team_historical_effective_sample_size": metadata.get("team_historical_effective_sample_size"),
        "home_away_prior_uncertainty": np.diag(prior_cov).tolist() if prior_cov is not None else None,
    }
    approved = (
        historical_prior_activation == "ACTIVE"
        and prior_packet is not None
        and prior_packet.get("status") == "VALID"
    )
    return {
        "gate_version": "MODEL_1-PRIOR-USEFULNESS-1.0.0",
        "decision": "USE_HISTORICAL_PRIOR" if approved else "USE_MARKET_ONLY",
        "reason": "ACTIVE_OOS_APPROVED_PRIOR" if approved else "CONSERVATIVE_NO_APPROVED_PRIOR_SUBSET",
        "runtime_target_fields_used": False,
        "threshold_source": "FROZEN_COMPETITION_OOS_ACTIVATION_NOT_FINAL_TEST_RETUNING",
        "features": features,
    }


def _historical_contract(
    out: dict[str, Any], *, activation: str, phase: str, usefulness: Mapping[str, Any]
) -> dict[str, Any]:
    posterior = out.get("posterior", {})
    predictive = out.get("posterior_predictive", {})
    market = posterior.get("market_likelihood", {})
    top3 = list(out.get("top3", []))
    median = list(posterior.get("median_lambda", []))
    out.update({
        "score_engine_mode": "HISTORICAL_BAYESIAN",
        "prior_used": True,
        "historical_prior_activation": activation,
        "market_cluster_status": market.get("status", "MISSING"),
        "market_cluster_used": market.get("status") == "VALID",
        "market_companies_used": list(market.get("companies_used", [])),
        "mean_log_lambda": posterior.get("mean_log_lambda"),
        "cov_log_lambda": posterior.get("cov_log_lambda"),
        "lambda_home": median[0] if len(median) > 0 else None,
        "lambda_away": median[1] if len(median) > 1 else None,
        "lambda_semantics": "MEDIAN_OF_LOGNORMAL_RATE_DISTRIBUTION",
        "rho": posterior.get("rho"),
        "execution_filtered_top3": top3,
        "Top1": top3[0] if len(top3) > 0 else None,
        "Top2": top3[1] if len(top3) > 1 else None,
        "Top3": top3[2] if len(top3) > 2 else None,
        "model_1x2": predictive.get("model_1x2"),
        "OU_references": _ou_references(predictive["grid"]) if predictive.get("grid") else {},
        "five_plus_home_tail": predictive.get("five_plus_home_tail"),
        "five_plus_away_tail": predictive.get("five_plus_away_tail"),
        "AH_gate_status": (
            "APPLIED_POSITIVE_SETTLEMENT_ONLY"
            if isinstance(out.get("execution_path", {}).get("ah"), Mapping)
            and out["execution_path"]["ah"].get("hard_gate")
            else "NOT_REQUESTED"
        ),
        "snapshot_phase": phase,
        "no_fake_historical_prior": True,
        "anti_double_counting": {
            "market_cluster_is_one_correlated_likelihood": True,
            "independent_bookmaker_votes": False,
            "historical_prior_is_market_blind": True,
            "prior_market_overlap": False,
        },
        "prior_usefulness_gate": dict(usefulness),
    })
    return out


def resolve_score_engine(
    competition: str,
    season: str,
    home_team: str,
    away_team: str,
    kickoff: str,
    quant_packet: Mapping[str, Any],
    snapshot_phase: str | None = None,
    *,
    mode: str = "AUTO",
    prior_store: Mapping[str, Any] | str | Path | None = None,
    prior_packet: Mapping[str, Any] | None = None,
    runtime_metadata: Mapping[str, Any] | None = None,
    context_updates: Sequence[Mapping[str, Any]] | None = None,
    execution_path: Mapping[str, Any] | None = None,
    market_absorbed_fraction: float = 0.0,
    market_sigma_floor: float = 0.12,
    max_goals: int = 12,
    draws: int = 4000,
) -> dict[str, Any]:
    """Unified production Stage14 resolver. AUTO is the formal default."""
    selected_mode = str(mode).strip().upper()
    if selected_mode not in SCORE_ENGINE_MODES:
        raise ValueError(f"Unknown score engine mode: {mode}")
    phase = _snapshot_phase(snapshot_phase, quant_packet)
    activation = _activation(prior_store, str(competition))
    explicit = prior_packet is not None
    if explicit:
        activation = str(prior_packet.get("activation", "ACTIVE"))

    context = {
        "competition": str(competition), "season": str(season),
        "home_team": str(home_team), "away_team": str(away_team),
        "kickoff": kickoff, "snapshot_phase": phase,
    }
    resolution_error = None
    candidate_prior = prior_packet
    wants_prior = selected_mode == "HISTORICAL_BAYESIAN" or (
        selected_mode == "AUTO" and activation == "ACTIVE"
    )
    if wants_prior and candidate_prior is None and prior_store is not None:
        try:
            candidate_prior = resolve_prior(context, prior_store, require_active=True)
        except PriorEngineError as exc:
            resolution_error = str(exc)

    if selected_mode == "HISTORICAL_BAYESIAN" and candidate_prior is None:
        return {
            "status": "MISSING", "reason": "BAYESIAN_PRIOR_REQUIRED",
            "detail": resolution_error, "score_engine_mode": "HISTORICAL_BAYESIAN",
            "prior_used": False, "historical_prior_activation": activation,
            "market_cluster_status": "NOT_EVALUATED", "market_companies_used": [],
            "snapshot_phase": phase, "top3": [], "execution_filtered_top3": [],
            "no_fake_historical_prior": True, "no_market_only_fallback": True,
        }

    usefulness = prior_usefulness_gate(
        quant_packet=quant_packet,
        historical_prior_activation=activation,
        prior_packet=candidate_prior,
        snapshot_phase=phase,
        runtime_metadata=runtime_metadata,
    )
    use_prior = selected_mode == "HISTORICAL_BAYESIAN" or (
        selected_mode == "AUTO" and usefulness["decision"] == "USE_HISTORICAL_PRIOR"
    )
    if use_prior:
        out = build_stage14_score_packet(
            quant_packet, candidate_prior,
            context_updates=context_updates,
            execution_path=_formal_execution_path(execution_path),
            market_absorbed_fraction=market_absorbed_fraction,
            market_sigma_floor=market_sigma_floor,
            max_goals=max_goals, draws=draws,
        )
        if out.get("status") not in {"BAYESIAN_POSTERIOR_TOP3", "SCORELINE_CONFLICT"}:
            out.setdefault("score_engine_mode", "HISTORICAL_BAYESIAN")
            out.setdefault("prior_used", False)
            out.setdefault("historical_prior_activation", activation)
            out.setdefault("snapshot_phase", phase)
            out.setdefault("no_fake_historical_prior", True)
            return out
        return _historical_contract(out, activation=activation, phase=phase, usefulness=usefulness)

    out = build_formal_market_score_packet(
        quant_packet,
        execution_path=_formal_execution_path(execution_path),
        historical_prior_activation=activation,
        snapshot_phase=phase,
        market_sigma_floor=market_sigma_floor,
        max_goals=max_goals,
        draws=draws,
    )
    out["prior_usefulness_gate"] = usefulness
    out["historical_prior_resolution_error"] = resolution_error
    return out
