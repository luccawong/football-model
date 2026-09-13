"""Runtime resolver for MODEL_1 Titan historical priors.

Supports legacy dense stores and the production compact store. Production models
keep a sparse penalised-posterior precision matrix and solve only the two fixture
log-rate directions Stage14 needs. The complete calibrated store may be packed as
LZMA+base85 text chunks; every chunk and the decoded payload are SHA256 checked.
Train-only process covariance is added to Laplace parameter uncertainty.

No market/current-context field is admitted here. Formal Stage14 requires an
ACTIVE competition; SHADOW/DISABLED/INSUFFICIENT_HISTORY remain research-only.
"""
from __future__ import annotations

import base64
from hashlib import sha256
import json
import lzma
from math import exp
from pathlib import Path
from typing import Any, Mapping
import zlib

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from gpt.prior_engine import FORBIDDEN_PRIOR_KEYS, PriorEngineError, _season_start, _utc_naive
from gpt.prior_competition import resolve_prior as _resolve_legacy_prior

KNOWN_ACTIVATIONS = {"ACTIVE", "SHADOW", "DISABLED", "INSUFFICIENT_HISTORY"}


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


def _read_checked_chunks(root: Path, parts: list[Mapping[str, Any]], label: str) -> bytes:
    chunks: list[str] = []
    for part in parts:
        part_path = (root / str(part["path"])).resolve()
        try:
            text = part_path.read_text(encoding="ascii")
        except OSError as exc:
            raise PriorEngineError(f"Prior chunk unavailable for {label}: {part_path}") from exc
        expected = part.get("sha256")
        if expected and sha256(text.encode("ascii")).hexdigest() != str(expected):
            raise PriorEngineError(f"Prior chunk checksum mismatch: {label} / {part_path.name}")
        chunks.append(text)
    try:
        return base64.b85decode("".join(chunks).encode("ascii"))
    except Exception as exc:
        raise PriorEngineError(f"Prior base85 decode failed for {label}.") from exc


def _decode_external_model(root: Path, competition: str, ref: Mapping[str, Any]) -> Mapping[str, Any]:
    if ref.get("path"):
        model_path = (root / str(ref["path"])).resolve()
        try:
            payload = json.loads(model_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise PriorEngineError(f"Prior model file unavailable for {competition}: {model_path}") from exc
    elif ref.get("encoding") == "ZLIB_BASE85_JSON" and isinstance(ref.get("parts"), list):
        try:
            raw = zlib.decompress(_read_checked_chunks(root, ref["parts"], competition))
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            if isinstance(exc, PriorEngineError):
                raise
            raise PriorEngineError(f"Packed prior model decode failed for {competition}.") from exc
        if ref.get("decoded_sha256") and sha256(raw).hexdigest() != str(ref["decoded_sha256"]):
            raise PriorEngineError(f"Prior model decoded checksum mismatch: {competition}")
    else:
        raise PriorEngineError(f"Unsupported prior model storage descriptor for {competition}.")
    loaded = payload.get("model") if isinstance(payload, Mapping) else None
    if str(payload.get("competition")) != competition or not isinstance(loaded, Mapping):
        raise PriorEngineError(f"Prior model file has invalid competition payload: {competition}")
    return loaded


def _decode_full_store(root: Path, descriptor: Mapping[str, Any]) -> dict[str, Any]:
    if descriptor.get("encoding") != "LZMA_BASE85_JSON" or not isinstance(descriptor.get("parts"), list):
        raise PriorEngineError("Unsupported packed prior-store descriptor.")
    try:
        raw = lzma.decompress(_read_checked_chunks(root, descriptor["parts"], "FULL_STORE"))
        decoded = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        if isinstance(exc, PriorEngineError):
            raise
        raise PriorEngineError("Packed prior-store decode failed.") from exc
    if descriptor.get("decoded_sha256") and sha256(raw).hexdigest() != str(descriptor["decoded_sha256"]):
        raise PriorEngineError("Packed prior-store decoded checksum mismatch.")
    if decoded.get("status") != "VALID" or not isinstance(decoded.get("competition_models"), Mapping):
        raise PriorEngineError("Decoded packed prior store is invalid.")
    return decoded


def _load_store_and_model(value: Mapping[str, Any] | str | Path, competition: str) -> tuple[dict[str, Any], Mapping[str, Any] | None]:
    if isinstance(value, Mapping):
        store = dict(value)
        models = store.get("competition_models") or store.get("league_models") or {}
        model = models.get(competition) if isinstance(models, Mapping) else None
        return store, model if isinstance(model, Mapping) else None

    path = Path(value)
    store = json.loads(path.read_text(encoding="utf-8"))
    models = store.get("competition_models") or store.get("league_models") or {}
    model = models.get(competition) if isinstance(models, Mapping) else None
    if isinstance(model, Mapping):
        return store, model

    packed = store.get("packed_store")
    if isinstance(packed, Mapping):
        decoded = _decode_full_store(path.parent, packed)
        decoded_models = decoded.get("competition_models", {})
        model = decoded_models.get(competition) if isinstance(decoded_models, Mapping) else None
        # Activation/status stays authoritative from the small manifest; decoded
        # payload supplies numerical model state only.
        return store, model if isinstance(model, Mapping) else None

    refs = store.get("model_files") or {}
    ref = refs.get(competition) if isinstance(refs, Mapping) else None
    if isinstance(ref, Mapping):
        return store, _decode_external_model(path.parent, competition, ref)
    return store, None


def _state_reference(model: Mapping[str, Any], state_map: Mapping[tuple[str, int], int], team: str, season_start: int) -> dict[str, Any]:
    hyper = model["hyperparameters"]
    current = state_map.get((team, season_start))
    if current is not None:
        return {"state_index": current, "innovation_variance": 0.0, "fallback": "CURRENT_SEASON"}
    previous = state_map.get((team, season_start - 1))
    if previous is not None:
        return {"state_index": previous, "innovation_variance": float(hyper["transition_sd"]) ** 2, "fallback": "PREVIOUS_SEASON_SHRINKAGE"}
    return {"state_index": None, "innovation_variance": float(hyper["team_sd"]) ** 2, "fallback": "COMPETITION_BASELINE_NEW_TEAM"}


def _pd2(cov: np.ndarray) -> tuple[np.ndarray, float]:
    cov = (np.asarray(cov, dtype=float) + np.asarray(cov, dtype=float).T) / 2.0
    if cov.shape != (2, 2) or not np.all(np.isfinite(cov)):
        raise PriorEngineError("Propagated log-lambda covariance is invalid.")
    eig = np.linalg.eigvalsh(cov)
    target = np.finfo(float).eps * max(1.0, float(np.trace(cov))) * 64.0
    jitter = max(0.0, target - float(np.min(eig)))
    if jitter:
        cov = cov + np.eye(2) * jitter
    if float(np.min(np.linalg.eigvalsh(cov))) <= 0.0:
        raise PriorEngineError("Could not obtain positive-definite log-lambda covariance.")
    return cov, jitter


def _resolve_compact(context: Mapping[str, Any], store: Mapping[str, Any], model: Mapping[str, Any], *, require_active: bool) -> dict[str, Any]:
    competition, target_season = _validated_context(context)
    status = store.get("competition_status", {}).get(competition, {})
    activation = str(status.get("activation", "SHADOW"))
    if activation not in KNOWN_ACTIVATIONS:
        raise PriorEngineError(f"Unknown prior activation for {competition}: {activation}")
    if require_active and activation != "ACTIVE":
        raise PriorEngineError(f"Competition prior is not formally active: {competition} ({activation})")

    precision = model.get("precision_csc")
    if not isinstance(precision, Mapping):
        raise PriorEngineError(f"Compact prior model missing precision matrix: {competition}")
    theta = np.asarray(model["theta"], dtype=float)
    layout = model["parameter_layout"]
    n = int(layout["state_count"])
    ao, do = int(layout["attack_offset"]), int(layout["defence_offset"])
    if do != ao + n:
        raise PriorEngineError("Stored compact parameter layout is inconsistent.")
    state_map = {(str(s["team"]), int(s["season_start"])): i for i, s in enumerate(model["states"])}
    hr = _state_reference(model, state_map, str(context["home_team"]), target_season)
    ar = _state_reference(model, state_map, str(context["away_team"]), target_season)

    xh, xa = np.zeros(len(theta)), np.zeros(len(theta))
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
    H = sparse.csc_matrix((np.asarray(precision["data"], float), np.asarray(precision["indices"], np.int32), np.asarray(precision["indptr"], np.int32)), shape=shape)
    if shape != (len(theta), len(theta)):
        raise PriorEngineError("Compact precision shape does not match theta.")
    try:
        cov = Xtarget @ splu(H).solve(Xtarget.T)
    except Exception as exc:
        raise PriorEngineError(f"Compact prior precision solve failed for {competition}.") from exc
    innovation = float(hr["innovation_variance"]) + float(ar["innovation_variance"])
    cov[0, 0] += innovation
    cov[1, 1] += innovation
    process_cov = np.asarray(model.get("process_cov_log_lambda", np.zeros((2, 2))), float)
    if process_cov.shape != (2, 2) or not np.all(np.isfinite(process_cov)):
        raise PriorEngineError(f"Invalid train-only process covariance for {competition}.")
    cov, jitter = _pd2(cov + process_cov)

    def sv(ref: Mapping[str, Any], offset: int) -> float:
        return 0.0 if ref["state_index"] is None else float(theta[offset + int(ref["state_index"])])

    mu, hfa = float(theta[int(layout["mu_league"])]), float(theta[int(layout["hfa_league"])])
    return {
        "status": "VALID",
        "engine_version": "MODEL_1-TITAN-PRIOR-RUNTIME-2.1.0",
        "mean_log_lambda": [float(mean[0]), float(mean[1])],
        "cov_log_lambda": cov.tolist(),
        "mean_lambda": [float(exp(mean[0])), float(exp(mean[1]))],
        "source_groups": ["TEAM_DATA"],
        "calibration_ref": store.get("calibration_ref"),
        "activation": activation,
        "components": {"mu_league": mu, "mu_competition": mu, "hfa_league": hfa, "hfa_competition": hfa, "attack_home": sv(hr, ao), "defense_home": sv(hr, do), "attack_away": sv(ar, ao), "defense_away": sv(ar, do), "x_beta_home": 0.0, "x_beta_away": 0.0},
        "fixture": {"competition": competition, "league": competition, "home_team": str(context["home_team"]), "away_team": str(context["away_team"]), "season": str(context["season"]), "season_start": target_season, "match_date": _utc_naive(context.get("match_date") or context.get("kickoff")).isoformat(sep=" ") if (context.get("match_date") or context.get("kickoff")) is not None else None},
        "hierarchy": {"home_team_fallback": hr["fallback"], "away_team_fallback": ar["fallback"], "half_life_days": float(model["hyperparameters"]["half_life_days"]), "team_sd": float(model["hyperparameters"]["team_sd"]), "transition_sd": float(model["hyperparameters"]["transition_sd"]), "opponent_adjusted": True, "partial_pooling": True, "competition_specific_baseline": True, "legacy_mu_league_semantics": "competition-specific scoring baseline"},
        "uncertainty": {"method": "LAPLACE_SPARSE_PRECISION_PROPAGATION_PLUS_TRAIN_ONLY_PROCESS_COVARIANCE", "process_cov_log_lambda": process_cov.tolist(), "numerical_pd_jitter": float(jitter), "fixed_score_covariance_forbidden": True},
        "anti_double_counting": {"market_inputs_used": False, "external_draw_label_used": False, "context_inputs_used": False, "process_covariance_train_only": True},
    }


def resolve_prior(context: Mapping[str, Any], store: Mapping[str, Any] | str | Path, *, require_active: bool = True) -> dict[str, Any]:
    """Resolve a formal/research Titan prior from dense or compact stores."""
    competition, _ = _validated_context(context)
    # Domestic V2 descriptors override only their named competition. European
    # numerical state and legacy explicit-prior callers retain their old paths.
    manifest = dict(store) if isinstance(store, Mapping) else json.loads(Path(store).read_text(encoding="utf-8"))
    domestic = manifest.get("domestic_v2", {}).get(competition)
    if isinstance(domestic, Mapping):
        return _resolve_domestic(context, manifest, domestic, store, require_active=require_active)
    loaded, model = _load_store_and_model(store, competition)
    if isinstance(model, Mapping) and isinstance(model.get("precision_csc"), Mapping):
        return _resolve_compact(context, loaded, model, require_active=require_active)
    if model is not None:
        loaded = dict(loaded)
        loaded.setdefault("competition_models", {})
        loaded["competition_models"] = dict(loaded["competition_models"])
        loaded["competition_models"][competition] = dict(model)
        loaded["league_models"] = dict(loaded.get("league_models") or loaded["competition_models"])
    return _resolve_legacy_prior(context, loaded, require_active=require_active)


def _resolve_domestic(context, manifest, descriptor, store, *, require_active):
    from gpt.domestic_prior import dynamic_packet

    phase = str(context.get("snapshot_phase", "closing")).lower()
    if phase not in {"opening", "closing"}:
        raise PriorEngineError("Domestic prior needs an opening or closing snapshot_phase")
    kickoff = context.get("kickoff") or context.get("match_date")
    if kickoff is None:
        raise PriorEngineError("Domestic dynamic prior requires kickoff")
    if "payload" in descriptor:
        payload = descriptor["payload"]
    else:
        if isinstance(store, Mapping):
            raise PriorEngineError("External domestic descriptor requires a store file path")
        root = Path(store).resolve().parent
        path = (root / descriptor["path"]).resolve()
        if not path.is_relative_to(root):
            raise PriorEngineError("Domestic model path escapes prior store")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise PriorEngineError("Domestic model file unavailable") from exc
        if sha256(raw).hexdigest() != descriptor.get("sha256"):
            raise PriorEngineError("Domestic model checksum mismatch")
        payload = json.loads(raw)
    competition = context.get("competition") or context.get("league")
    if payload.get("competition") != competition:
        raise PriorEngineError("Domestic model competition mismatch")
    activation = payload.get("oos", {}).get("activation", {})
    overall = manifest.get("competition_status", {}).get(competition, {}).get("activation", "SHADOW")
    if require_active and (overall != "ACTIVE" or activation.get(phase, {}).get("status") != "ACTIVE"):
        raise PriorEngineError(f"Competition prior is not formally active: {competition} / {phase}")
    frozen = payload["frozen"]
    if require_active and (frozen["selected"]["boundary"] or frozen["trust"][phase]["boundary"]):
        raise PriorEngineError("Domestic Train boundary is unresolved")
    if require_active:
        from gpt.domestic_gate import activation_gate
        evidence = activation_gate(payload["oos"]["validation"], payload["oos"]["test"],
                                   frozen["selected"], frozen["trust"])
        if evidence[phase]["status"] != "ACTIVE":
            raise PriorEngineError("Domestic OOS evidence does not pass the release gate")
    packet = dynamic_packet(payload["model"], str(context["home_team"]), str(context["away_team"]),
                            str(context["season"]), kickoff, frozen["trust"][phase])
    packet["activation"] = overall
    packet["snapshot_phase"] = phase
    packet["lifecycle"] = activation.get("lifecycle", "SHADOW")
    return packet


class DomesticPriorResolver:
    """Bound metadata-only API; prices remain downstream of this resolver."""
    def __init__(self, store, *, snapshot_phase="closing"):
        self.store = store
        self.snapshot_phase = snapshot_phase

    def resolve_prior(self, competition, season, home_team, away_team, kickoff):
        return resolve_prior({"competition": competition, "season": season,
                              "home_team": home_team, "away_team": away_team,
                              "kickoff": kickoff, "snapshot_phase": self.snapshot_phase}, self.store)
