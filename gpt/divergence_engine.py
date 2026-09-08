"""Defensive / lead-lag / attraction-adjusted market divergence utilities.

This layer is deliberately RESEARCH_ONLY_UNCALIBRATED.  It measures whether a
selected outcome is priced more defensively by a secondary/non-consensus book
cluster than by the mainstream cluster.  It never converts that observation
into a match probability adjustment or a betting grade.

Inputs must already be aligned to the same time slice and de-vigged.  Feed
independence, attraction and cross-market confirmation are explicit inputs so
post-result narrative cannot be silently substituted for missing evidence.
"""
from __future__ import annotations

from math import isfinite
from statistics import mean
from typing import Any, Mapping, Sequence

DIVERGENCE_ENGINE_VERSION = "DDS-FOOTBALL-1.0.0"
STATUS = "RESEARCH_ONLY_UNCALIBRATED"


class DivergenceInputError(ValueError):
    pass


def _prob3(row: Sequence[float]) -> tuple[float, float, float]:
    if len(row) != 3:
        raise DivergenceInputError("1X2 rows must contain home/draw/away probabilities")
    vals = tuple(float(x) for x in row)
    if any((not isfinite(x) or x < 0) for x in vals):
        raise DivergenceInputError("probabilities must be finite and non-negative")
    total = sum(vals)
    if total <= 0:
        raise DivergenceInputError("probability mass must be positive")
    return tuple(x / total for x in vals)


def _target_probability(row: Sequence[float], target: str, favorite_side: str | None) -> float:
    home, draw, away = _prob3(row)
    key = str(target).strip().upper()
    if key == "HOME":
        return home
    if key == "DRAW":
        return draw
    if key == "AWAY":
        return away
    if key == "FAVORITE_NONWIN":
        fav = str(favorite_side or "").strip().upper()
        if fav == "HOME":
            return draw + away
        if fav == "AWAY":
            return home + draw
        raise DivergenceInputError("favorite_side must be HOME or AWAY for FAVORITE_NONWIN")
    raise DivergenceInputError("target must be HOME, DRAW, AWAY or FAVORITE_NONWIN")


def _lead_lag(lead_minutes: float | None, mainstream_followed: bool | None) -> str:
    if lead_minutes is None:
        return "UNKNOWN"
    lead = float(lead_minutes)
    if not isfinite(lead):
        raise DivergenceInputError("lead_minutes must be finite")
    if lead > 0:
        if mainstream_followed is True:
            return "LEADING_CONFIRMED"
        if mainstream_followed is False:
            return "LEADING_UNCONFIRMED"
        return "LEADING_UNKNOWN_FOLLOW"
    if lead < 0:
        return "LAGGING"
    return "COINCIDENT"


def assess_football_divergence(
    *,
    mainstream_rows: Sequence[Sequence[float]],
    secondary_rows: Sequence[Sequence[float]],
    target: str,
    attraction_score: float,
    persistence_minutes: float,
    independent_clusters: int,
    favorite_side: str | None = None,
    lead_minutes: float | None = None,
    mainstream_followed: bool | None = None,
    cross_market_confirmations: int = 0,
    copied_feed: bool = False,
    frozen_at: str | None = None,
) -> Mapping[str, Any]:
    """Assess one football defensive-pricing divergence signal.

    Positive ``magnitude_pp`` means the secondary cluster assigns more de-vigged
    probability to the selected target than the mainstream cluster does.
    ``attraction_score`` is 0-100, where higher means the target has more natural
    betting attraction.  The UDS flag therefore requires *low* attraction.
    """
    if not mainstream_rows or not secondary_rows:
        raise DivergenceInputError("both mainstream_rows and secondary_rows are required")
    attraction = float(attraction_score)
    persistence = float(persistence_minutes)
    clusters = int(independent_clusters)
    confirmations = int(cross_market_confirmations)
    if not (isfinite(attraction) and 0 <= attraction <= 100):
        raise DivergenceInputError("attraction_score must be between 0 and 100")
    if not (isfinite(persistence) and persistence >= 0):
        raise DivergenceInputError("persistence_minutes must be non-negative")
    if clusters < 1 or confirmations < 0:
        raise DivergenceInputError("cluster and confirmation counts are invalid")

    mainstream = [_target_probability(r, target, favorite_side) for r in mainstream_rows]
    secondary = [_target_probability(r, target, favorite_side) for r in secondary_rows]
    main_mean = mean(mainstream)
    secondary_mean = mean(secondary)
    magnitude_pp = (secondary_mean - main_mean) * 100.0
    lead_lag = _lead_lag(lead_minutes, mainstream_followed)

    low_attraction = attraction <= 40.0
    uds = bool(
        not copied_feed
        and magnitude_pp >= 2.0
        and low_attraction
        and persistence >= 20.0
        and clusters >= 2
    )

    if copied_feed or abs(magnitude_pp) < 1.0:
        grade = "NOISE"
    elif (
        uds
        and magnitude_pp >= 3.0
        and persistence >= 30.0
        and confirmations >= 1
        and lead_lag == "LEADING_CONFIRMED"
    ):
        grade = "A"
    elif uds and (confirmations >= 1 or lead_lag.startswith("LEADING")):
        grade = "B"
    else:
        grade = "C"

    target_key = str(target).strip().upper()
    return {
        "version": DIVERGENCE_ENGINE_VERSION,
        "status": STATUS,
        "target": target_key,
        "favorite_side": str(favorite_side).upper() if favorite_side else None,
        "mainstream_target_probability": main_mean,
        "secondary_target_probability": secondary_mean,
        "magnitude_pp": magnitude_pp,
        "direction": "DEFENSIVE_TO_TARGET" if magnitude_pp > 0 else "NOT_DEFENSIVE_TO_TARGET",
        "attraction_score": attraction,
        "low_attraction": low_attraction,
        "persistence_minutes": persistence,
        "independent_clusters": clusters,
        "lead_lag": lead_lag,
        "cross_market_confirmations": confirmations,
        "copied_feed": bool(copied_feed),
        "uds_unnatural_defensive_signal": uds,
        "information_grade": grade,
        "same_time_slice_required": True,
        "devig_required": True,
        "frozen_at": frozen_at,
        "probability_adjustment": None,
        "ticket_grade": None,
        "note": "Information-quality flag only. Validate prospectively before any probability or ticket-weight use.",
    }
