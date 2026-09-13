"""Competition-aware orchestration for the MODEL_1 Titan historical prior.

The lower-level numerical engine in :mod:`gpt.prior_engine` keeps the historical
``league``/``mu_league`` field names for backward compatibility. In this module
those fields have competition semantics: each distinct Titan ``competition`` is
fitted, calibrated and activated independently. No market or current-context
inputs are admitted to the prior.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any, Mapping, Sequence

from gpt.prior_engine import (
    FORBIDDEN_PRIOR_KEYS,
    HyperParameters,
    PriorEngineError,
    _season_start,
    _utc_naive,
    audit_titan_sqlite,
    build_prior_packet_from_model,
    fit_league_model,
)

COMPETITION_LAYER_VERSION = "MODEL_1-TITAN-COMPETITION-LAYER-1.0.0"
FORMAL_ACTIVATIONS = {"ACTIVE"}
KNOWN_ACTIVATIONS = {"ACTIVE", "SHADOW", "DISABLED", "INSUFFICIENT_HISTORY"}


def file_sha256(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    h = sha256()
    with Path(path).open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _q(identifier: str) -> str:
    return '"' + str(identifier).replace('"', '""') + '"'


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def audit_competition_coverage(
    db_path: str | Path,
    *,
    min_completed_matches: int = 80,
    min_oos_seasons: int = 4,
) -> dict[str, Any]:
    """Audit every distinct raw competition without silently dropping bad rows."""
    audit = audit_titan_sqlite(db_path)
    if audit.get("status") != "VALID":
        raise PriorEngineError(f"Titan database audit failed: {audit}")
    mapping = audit["field_mapping"]
    cols = [mapping[k] for k in (
        "match_id", "match_date", "league", "season", "home_team", "away_team",
        "home_score", "away_score",
    )]
    select = ", ".join(_q(c) for c in cols)
    con = sqlite3.connect(str(db_path))
    try:
        raw = con.execute(f"SELECT {select} FROM matches").fetchall()
    finally:
        con.close()

    groups: dict[str, dict[str, Any]] = {}
    season_groups: dict[tuple[str, str], dict[str, Any]] = {}
    for row in raw:
        (_mid, raw_date, raw_comp, raw_season, home, away, hg, ag) = row
        comp = "" if raw_comp is None else str(raw_comp).strip()
        season = "" if raw_season is None else str(raw_season).strip()
        key = comp
        skey = (comp, season)
        if key not in groups:
            groups[key] = {
                "competition": comp, "matches": 0, "completed_matches": 0,
                "missing_scores": 0, "dates": [], "teams": set(),
                "home_goals": [], "away_goals": [], "seasons": set(),
            }
        if skey not in season_groups:
            season_groups[skey] = {
                "competition": comp, "season": season, "matches": 0,
                "completed_matches": 0, "missing_scores": 0, "dates": [],
                "teams": set(), "home_goals": [], "away_goals": [],
            }
        for bucket in (groups[key], season_groups[skey]):
            bucket["matches"] += 1
            if raw_date is not None:
                bucket["dates"].append(str(raw_date))
            if home is not None and str(home).strip():
                bucket["teams"].add(str(home).strip())
            if away is not None and str(away).strip():
                bucket["teams"].add(str(away).strip())
            h = _safe_float(hg)
            a = _safe_float(ag)
            if h is None or a is None or h < 0 or a < 0:
                bucket["missing_scores"] += 1
            else:
                bucket["completed_matches"] += 1
                bucket["home_goals"].append(h)
                bucket["away_goals"].append(a)
        groups[key]["seasons"].add(season)

    def finish(bucket: Mapping[str, Any], *, include_seasons: bool) -> dict[str, Any]:
        home_goals = list(bucket["home_goals"])
        away_goals = list(bucket["away_goals"])
        dates = list(bucket["dates"])
        out = {
            "competition": bucket["competition"],
            "matches": int(bucket["matches"]),
            "completed_matches": int(bucket["completed_matches"]),
            "first_date": min(dates) if dates else None,
            "last_date": max(dates) if dates else None,
            "distinct_teams": len(bucket["teams"]),
            "home_goals_mean": (sum(home_goals) / len(home_goals)) if home_goals else None,
            "away_goals_mean": (sum(away_goals) / len(away_goals)) if away_goals else None,
            "total_goals_mean": ((sum(home_goals) + sum(away_goals)) / len(home_goals)) if home_goals else None,
            "missing_scores": int(bucket["missing_scores"]),
        }
        if include_seasons:
            seasons = sorted((s for s in bucket["seasons"] if s), key=_season_start)
            out["seasons"] = seasons
            if not bucket["competition"]:
                status, reason = "DATA_QUALITY_FAIL", "EMPTY_COMPETITION"
            elif out["completed_matches"] < int(min_completed_matches):
                status, reason = "INSUFFICIENT_HISTORY", "TOO_FEW_COMPLETED_MATCHES"
            elif len(seasons) < int(min_oos_seasons):
                status, reason = "VALID_WITH_LIMITATIONS", "INSUFFICIENT_OOS_HISTORY"
            elif out["missing_scores"] > 0:
                status, reason = "VALID_WITH_LIMITATIONS", "MISSING_SCORE_ROWS_EXCLUDED"
            else:
                status, reason = "VALID", "OK"
            out["prior_status"] = status
            out["reason"] = reason
            out["usable_for_prior"] = status in {"VALID", "VALID_WITH_LIMITATIONS"}
        return out

    competition_rows = [finish(groups[k], include_seasons=True) for k in sorted(groups)]
    season_rows = []
    def season_sort_key(item: tuple[str, str]) -> tuple[str, int]:
        comp, season = item
        try:
            start = _season_start(season)
        except PriorEngineError:
            start = -1
        return comp, start
    for key in sorted(season_groups, key=season_sort_key):
        item = finish(season_groups[key], include_seasons=False)
        item["season"] = key[1]
        season_rows.append(item)
    return {
        "status": "VALID",
        "competition_universe": [r["competition"] for r in competition_rows],
        "competition_count": len(competition_rows),
        "competition_coverage": competition_rows,
        "competition_season_coverage": season_rows,
    }


def competition_split(
    rows: Sequence[Mapping[str, Any]],
    competition: str,
    *,
    min_oos_seasons: int = 4,
) -> dict[str, Any]:
    by_start: dict[int, str] = {}
    for row in rows:
        if str(row["league"]) != str(competition):
            continue
        by_start.setdefault(int(row["season_start"]), str(row["season"]))
    ordered = [by_start[k] for k in sorted(by_start)]
    if len(ordered) < int(min_oos_seasons):
        return {
            "status": "INSUFFICIENT_OOS_HISTORY", "competition": str(competition),
            "seasons": ordered,
            "train": ordered[:-2] if len(ordered) >= 3 else [],
            "validate": ordered[-2:-1] if len(ordered) >= 2 else [],
            "test": ordered[-1:] if ordered else [],
        }
    return {
        "status": "VALID", "competition": str(competition), "seasons": ordered,
        "train": ordered[:-2], "validate": [ordered[-2]], "test": [ordered[-1]],
    }


def fit_competition_model(
    rows: Sequence[Mapping[str, Any]],
    *, competition: str, as_of: str | datetime,
    hyperparameters: HyperParameters, min_matches: int = 80,
) -> dict[str, Any]:
    model = fit_league_model(
        rows, league=str(competition), as_of=as_of,
        hyperparameters=hyperparameters, min_matches=min_matches,
    )
    model = dict(model)
    model["competition"] = str(competition)
    model["legacy_api_field_note"] = (
        "league/mu_league/hfa_league are retained API field names; semantic scope is competition-specific"
    )
    return model


def build_competition_store(
    rows: Sequence[Mapping[str, Any]],
    *,
    hyperparameters_by_competition: Mapping[str, Mapping[str, float]],
    competition_status: Mapping[str, Mapping[str, Any]],
    as_of: str | datetime,
    dataset_audit: Mapping[str, Any],
    calibration: Mapping[str, Any],
    min_matches: int = 80,
) -> dict[str, Any]:
    cutoff = _utc_naive(as_of)
    models: dict[str, Any] = {}
    failures: dict[str, str] = {}
    for competition, raw in hyperparameters_by_competition.items():
        try:
            hyper = HyperParameters(float(raw["half_life_days"]), float(raw["team_sd"]), float(raw["transition_sd"]))
            models[str(competition)] = fit_competition_model(
                rows, competition=str(competition), as_of=cutoff,
                hyperparameters=hyper, min_matches=min_matches,
            )
        except Exception as exc:
            failures[str(competition)] = f"{type(exc).__name__}: {exc}"

    status_map = {str(k): dict(v) for k, v in competition_status.items()}
    for competition, reason in failures.items():
        status_map.setdefault(competition, {})
        status_map[competition].update({"activation": "SHADOW", "reason": "FINAL_FIT_FAILED", "detail": reason})

    provenance = {
        "competition_layer_version": COMPETITION_LAYER_VERSION,
        "dataset_sha256": dataset_audit.get("dataset_sha256"),
        "dataset_rows": dataset_audit.get("matches_count"),
        "training_cutoff": cutoff.isoformat(sep=" "),
        "competitions": sorted(status_map),
        "calibrated_models": sorted(models),
    }
    fingerprint = sha256(json.dumps(provenance, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "store_version": "MODEL_1-TITAN-PRIOR-STORE-2.0.0",
        "status": "VALID",
        "created_from": "TITAN_HISTORICAL_MATCH_RESULTS_ONLY",
        "as_of": cutoff.isoformat(sep=" "),
        "dataset_audit": dict(dataset_audit),
        "calibration": dict(calibration),
        "calibration_ref": f"MODEL_1-TITAN-PRIOR-STORE-2.0.0:{fingerprint[:16]}",
        "competition_status": status_map,
        "competition_models": models,
        "league_models": models,
        "legacy_field_semantics": {
            "league": "competition",
            "mu_league": "competition-specific scoring baseline",
            "hfa_league": "competition-specific home-field advantage",
        },
        "forbidden_sources": [
            "Pinnacle", "Bet365", "Macau", "William Hill", "Ladbrokes", "HKJC", "Interwetten",
            "1X2", "AH", "OU", "Betfair", "DRAW_EXCLUSION", "JCB", "LINEUP", "INJURY", "OFF_FIELD",
        ],
    }


def save_competition_store(store: Mapping[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def load_competition_store(value: Mapping[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, Mapping):
        store = dict(value)
    else:
        store = json.loads(Path(value).read_text(encoding="utf-8"))
    models = store.get("competition_models") or store.get("league_models")
    if store.get("status") != "VALID" or not isinstance(models, Mapping):
        raise PriorEngineError("Prior store is missing or invalid.")
    store["competition_models"] = dict(models)
    return store


def resolve_prior(
    context: Mapping[str, Any],
    store: Mapping[str, Any] | str | Path,
    *, require_active: bool = True,
) -> dict[str, Any]:
    """Resolve one competition-specific historical prior for formal Stage14."""
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

    loaded = load_competition_store(store)
    name = str(competition)
    status = loaded.get("competition_status", {}).get(name)
    if status is not None:
        activation = str(status.get("activation", "SHADOW"))
        if activation not in KNOWN_ACTIVATIONS:
            raise PriorEngineError(f"Unknown prior activation for {name}: {activation}")
        if require_active and activation not in FORMAL_ACTIVATIONS:
            raise PriorEngineError(f"Competition prior is not formally active: {name} ({activation})")
    model = loaded["competition_models"].get(name)
    if not isinstance(model, Mapping):
        raise PriorEngineError(f"No calibrated Titan prior model for competition: {name}")

    packet = build_prior_packet_from_model(
        model,
        home_team=str(context["home_team"]), away_team=str(context["away_team"]),
        season=context["season"],
        match_date=context.get("match_date") or context.get("kickoff"),
        calibration_ref=loaded.get("calibration_ref"),
    )
    packet = dict(packet)
    packet["fixture"] = dict(packet["fixture"])
    packet["fixture"]["competition"] = name
    packet["components"] = dict(packet["components"])
    packet["components"]["mu_competition"] = packet["components"]["mu_league"]
    packet["components"]["hfa_competition"] = packet["components"]["hfa_league"]
    packet["hierarchy"] = dict(packet["hierarchy"])
    packet["hierarchy"]["competition_specific_baseline"] = True
    packet["hierarchy"]["legacy_mu_league_semantics"] = "competition-specific scoring baseline"
    packet["activation"] = status.get("activation") if isinstance(status, Mapping) else "LEGACY_COMPATIBLE"
    return packet
