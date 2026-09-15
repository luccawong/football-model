"""Leakage-safe RECENT_FORM V1 feature and artifact helpers.

This module is deliberately research-layer only.  It prepares an observation
about the *pre-kickoff* log scoring rates, but it never changes a Stage14
weight by itself.  The runtime bridge below accepts only a per-competition,
per-market-phase artifact whose release gate is ``APPROVED_PRODUCTION``.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from math import exp, isfinite, log
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np


VERSION = "MODEL_1-RECENT-FORM-1.0.0"
ARTIFACT_VERSION = "MODEL_1-RECENT-FORM-CALIBRATION-1.0.0"
APPROVED_STATUS = "APPROVED_PRODUCTION"


class RecentFormError(ValueError):
    """Raised when a recent-form artifact or input violates its contract."""


@dataclass(frozen=True)
class RecentMatch:
    match_id: str
    kickoff: datetime
    league: str
    season_start: int
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int


def _finite_vector(value: Any, name: str, n: int) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (n,) or not np.all(np.isfinite(array)):
        raise RecentFormError(f"{name} must be a finite length-{n} vector")
    return array


def _finite_covariance(value: Any, name: str = "cov_log_lambda") -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (2, 2) or not np.all(np.isfinite(array)):
        raise RecentFormError(f"{name} must be a finite 2x2 matrix")
    if not np.allclose(array, array.T, atol=1e-10) or np.min(np.linalg.eigvalsh(array)) <= 0:
        raise RecentFormError(f"{name} must be symmetric positive definite")
    return array


def canonical_json_sha256(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


class RecentFormFeatureBuilder:
    """Build pre-match recent-form features with a strict timestamp cutoff.

    ``transform`` processes identical kickoffs as a batch: no target at a
    kickoff can observe another result at that same kickoff.  Every stored
    source record is asserted to be strictly older than the target kickoff.
    Attack and defense use home/away-specific histories with an all-venue
    fallback, opponent-normalised at the target's information set, calendar
    decay, a finite last-N window, and league-rate shrinkage.
    """

    def __init__(self, *, window: int, half_life_days: float, shrinkage_matches: float) -> None:
        if window not in {5, 10}:
            raise RecentFormError("window must be 5 or 10")
        if half_life_days <= 0 or shrinkage_matches < 0:
            raise RecentFormError("half_life_days must be > 0 and shrinkage_matches >= 0")
        self.window = int(window)
        self.half_life_days = float(half_life_days)
        self.shrinkage_matches = float(shrinkage_matches)

    @staticmethod
    def _season_prior(event: RecentMatch, target: RecentMatch) -> float:
        """Current-season preference with cross-season promoted-team fallback."""
        return 1.0 if event.season_start == target.season_start else 0.45

    def _team_rate(
        self,
        *,
        events: list[RecentMatch], team: str, venue: str, target: RecentMatch,
        league_home_rate: float, league_away_rate: float,
    ) -> tuple[float, float, float, bool]:
        """Return attack, defensive-concession, effective N, promoted fallback."""
        venue_events = [
            e for e in events
            if (e.home_team == team if venue == "home" else e.away_team == team)
        ]
        fallback = not venue_events
        source = venue_events or [e for e in events if team in (e.home_team, e.away_team)]
        source = source[-self.window:]
        if not source:
            return 0.0, 0.0, 0.0, True

        attack_num = defense_num = denom = 0.0
        for event in source:
            if event.kickoff >= target.kickoff:
                raise RecentFormError("RECENT_FORM_FUTURE_LEAKAGE")
            age = max(0.0, (target.kickoff - event.kickoff).total_seconds() / 86400.0)
            weight = exp(-log(2.0) * age / self.half_life_days) * self._season_prior(event, target)
            if event.home_team == team:
                gf, ga, opponent = event.home_goals, event.away_goals, event.away_team
            else:
                gf, ga, opponent = event.away_goals, event.home_goals, event.home_team
            # Opponent adjustment uses only its pre-target historical record;
            # no target/future result is included in this information set.
            opponent_events = [x for x in events if opponent in (x.home_team, x.away_team)]
            if opponent_events:
                opponent_ga = []
                opponent_gf = []
                for x in opponent_events:
                    if x.home_team == opponent:
                        opponent_ga.append(x.away_goals); opponent_gf.append(x.home_goals)
                    else:
                        opponent_ga.append(x.home_goals); opponent_gf.append(x.away_goals)
                opp_concede = (sum(opponent_ga) + self.shrinkage_matches * league_away_rate) / (len(opponent_ga) + self.shrinkage_matches)
                opp_attack = (sum(opponent_gf) + self.shrinkage_matches * league_home_rate) / (len(opponent_gf) + self.shrinkage_matches)
            else:
                opp_concede, opp_attack = league_away_rate, league_home_rate
            attack_num += weight * gf / max(0.20, opp_concede / max(0.20, league_away_rate))
            defense_num += weight * ga / max(0.20, opp_attack / max(0.20, league_home_rate))
            denom += weight
        base_attack = league_home_rate if venue == "home" else league_away_rate
        base_defense = league_away_rate if venue == "home" else league_home_rate
        attack = (attack_num + self.shrinkage_matches * base_attack) / (denom + self.shrinkage_matches)
        defense = (defense_num + self.shrinkage_matches * base_defense) / (denom + self.shrinkage_matches)
        return log(max(0.20, attack / base_attack)), log(max(0.20, defense / base_defense)), denom, fallback

    def transform(self, matches: Iterable[RecentMatch]) -> dict[str, dict[str, Any]]:
        ordered = sorted(matches, key=lambda item: (item.kickoff, item.match_id))
        histories: dict[str, list[RecentMatch]] = defaultdict(list)
        league_history: dict[str, list[RecentMatch]] = defaultdict(list)
        result: dict[str, dict[str, Any]] = {}
        cursor = 0
        while cursor < len(ordered):
            kickoff = ordered[cursor].kickoff
            batch: list[RecentMatch] = []
            while cursor < len(ordered) and ordered[cursor].kickoff == kickoff:
                batch.append(ordered[cursor]); cursor += 1
            for target in batch:
                league_events = league_history[target.league]
                if league_events:
                    home_rate = (sum(x.home_goals for x in league_events) + 5.0 * 1.35) / (len(league_events) + 5.0)
                    away_rate = (sum(x.away_goals for x in league_events) + 5.0 * 1.10) / (len(league_events) + 5.0)
                else:
                    home_rate, away_rate = 1.35, 1.10
                ha, hd, hn, hp = self._team_rate(events=histories[target.home_team], team=target.home_team, venue="home", target=target, league_home_rate=home_rate, league_away_rate=away_rate)
                aa, ad, an, ap = self._team_rate(events=histories[target.away_team], team=target.away_team, venue="away", target=target, league_home_rate=home_rate, league_away_rate=away_rate)
                result[target.match_id] = {
                    "features": [ha, ad, aa, hd],
                    "feature_names": ["home_attack", "away_defense", "away_attack", "home_defense"],
                    "effective_samples": {"home": hn, "away": an},
                    "promoted_team_fallback": {"home": hp, "away": ap},
                    "strict_cutoff": target.kickoff.isoformat(),
                    "source_match_kickoff_rule": "source_match_kickoff < target_match_kickoff",
                }
            for event in batch:
                histories[event.home_team].append(event)
                histories[event.away_team].append(event)
                league_history[event.league].append(event)
        return result


def load_approved_recent_form_artifact(
    root: str | Path, *, competition: str, market_phase: str,
) -> dict[str, Any] | None:
    """Load only a production-approved artifact; SHADOW never reaches runtime."""
    path = Path(root) / f"{competition}_{market_phase.lower()}.json"
    if not path.exists():
        return None
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if artifact.get("artifact_version") != ARTIFACT_VERSION:
        raise RecentFormError("RECENT_FORM_ARTIFACT_VERSION_MISMATCH")
    if artifact.get("competition") != competition or str(artifact.get("market_phase", "")).upper() != market_phase.upper():
        raise RecentFormError("RECENT_FORM_ARTIFACT_SCOPE_MISMATCH")
    if artifact.get("activation") != APPROVED_STATUS or not artifact.get("runtime_eligible", False):
        return None
    expected = artifact.get("artifact_sha256")
    unsigned = dict(artifact); unsigned.pop("artifact_sha256", None)
    if expected != canonical_json_sha256(unsigned):
        raise RecentFormError("RECENT_FORM_ARTIFACT_HASH_MISMATCH")
    _finite_vector(artifact.get("coefficients"), "coefficients", 4)
    _finite_vector(artifact.get("intercept"), "intercept", 2)
    _finite_covariance(artifact.get("cov_log_lambda"))
    return artifact


def recent_form_observation(
    artifact: Mapping[str, Any], feature_row: Mapping[str, Any], *, evidence_timestamp: str,
    context_snapshot_timestamp: str, kickoff: str, base_mean_log_lambda: Any,
) -> dict[str, Any]:
    """Build a validated Stage14 context observation from an approved artifact."""
    if artifact.get("activation") != APPROVED_STATUS or not artifact.get("runtime_eligible", False):
        raise RecentFormError("RECENT_FORM_ARTIFACT_NOT_APPROVED")
    features = _finite_vector(feature_row.get("features"), "features", 4)
    coefficients = _finite_vector(artifact.get("coefficients"), "coefficients", 4)
    intercept = _finite_vector(artifact.get("intercept"), "intercept", 2)
    # Separate home/away response coefficients are encoded in two rows in the
    # artifact; the first four-vector is a shared compact representation only
    # for provenance, while response_coefficients drives the actual update.
    response = np.asarray(artifact.get("response_coefficients"), dtype=float)
    if response.shape != (2, 4) or not np.all(np.isfinite(response)):
        raise RecentFormError("response_coefficients must be finite 2x4")
    scaler = artifact.get("robust_scaler", {})
    center = _finite_vector(scaler.get("center"), "robust_scaler.center", 4)
    scale = _finite_vector(scaler.get("scale"), "robust_scaler.scale", 4)
    if np.any(scale <= 0):
        raise RecentFormError("robust_scaler.scale must be positive")
    # The response is a residual observation around the exact current Stage14
    # market-cluster centre; it is not a second historical prior.
    mean = _finite_vector(base_mean_log_lambda, "base_mean_log_lambda", 2) + intercept + response @ ((features - center) / scale)
    return {
        "source_group": "RECENT_FORM", "effect_mode": "QUANTIFIED_OBSERVATION",
        "validated": True, "calibration_status": APPROVED_STATUS,
        "calibration_ref": artifact["calibration_ref"], "calibration_version": artifact["calibration_version"],
        "mean_log_lambda": mean.tolist(), "cov_log_lambda": _finite_covariance(artifact["cov_log_lambda"]).tolist(),
        "evidence_timestamp": evidence_timestamp, "context_snapshot_timestamp": context_snapshot_timestamp,
        "kickoff": kickoff, "historical_overlap_fraction": 0.0, "absorbed_fraction": 0.0,
        "provenance": {"artifact_sha256": artifact["artifact_sha256"], "source_group": "RECENT_FORM", "not_in_historical_prior": True},
        "source_match_kickoff_rule": "source_match_kickoff < target_match_kickoff",
    }


def build_approved_recent_form_context_updates(
    *, artifact_root: str | Path, competition: str, market_phase: str,
    feature_row: Mapping[str, Any], base_mean_log_lambda: Any,
    evidence_timestamp: str, context_snapshot_timestamp: str, kickoff: str,
    market_snapshot_timestamp: str | None = None,
) -> dict[str, Any]:
    """Route RECENT_FORM through the existing Prematch Context contract.

    The bridge deliberately returns an empty update for a SHADOW, missing, or
    non-approved artifact.  Callers therefore cannot accidentally turn a
    research artifact into a Stage14 mean shift by merely passing a path.
    """
    from gpt.prematch_context import build_prematch_context_updates

    artifact = load_approved_recent_form_artifact(
        artifact_root, competition=competition, market_phase=market_phase,
    )
    if artifact is None:
        return build_prematch_context_updates(
            kickoff=kickoff, context_snapshot_timestamp=context_snapshot_timestamp,
            market_snapshot_timestamp=market_snapshot_timestamp,
        )
    observation = recent_form_observation(
        artifact, feature_row, evidence_timestamp=evidence_timestamp,
        context_snapshot_timestamp=context_snapshot_timestamp, kickoff=kickoff,
        base_mean_log_lambda=base_mean_log_lambda,
    )
    return build_prematch_context_updates(
        recent_form=observation, kickoff=kickoff,
        context_snapshot_timestamp=context_snapshot_timestamp,
        market_snapshot_timestamp=market_snapshot_timestamp,
        calibration_ref=artifact["calibration_ref"], calibration_status=APPROVED_STATUS,
        calibration_version=artifact["calibration_version"],
        provenance=observation["provenance"],
    )


__all__ = [
    "APPROVED_STATUS", "ARTIFACT_VERSION", "RecentFormError", "RecentFormFeatureBuilder",
    "RecentMatch", "VERSION", "build_approved_recent_form_context_updates", "canonical_json_sha256", "load_approved_recent_form_artifact",
    "recent_form_observation",
]
