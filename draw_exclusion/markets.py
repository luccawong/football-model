"""Market-scoped teacher evidence. A fixture identity is never a label key."""
from __future__ import annotations

MARKETS = ("JC", "BD")


def require_market(market: str) -> str:
    if market not in MARKETS:
        raise ValueError("market must explicitly be JC or BD")
    return market


def market_key(research_match_id: str, market: str) -> str:
    return f"{research_match_id}|{require_market(market)}"


def layer(market: str, entry: dict | None = None) -> dict:
    prefix = require_market(market).lower()
    entry = entry or {}
    return {
        f"{prefix}_draw_exclusion_label": entry.get("external_draw_exclusion_label"),
        f"{prefix}_status": entry.get("status", "NOT_IN_SOURCE_POOL"),
        f"{prefix}_snapshot_id": entry.get("snapshot_id"),
        f"{prefix}_snapshot_time": entry.get("snapshot_time"),
        f"{prefix}_source": entry.get("source"),
        f"{prefix}_provenance": entry.get("provenance", []),
    }


def scoped_result(market: str, entry: dict) -> dict:
    require_market(market)
    return {**entry, "market": market, "source_market": market,
            "label": entry.get("external_draw_exclusion_label"),
            f"{market}_layer": layer(market, entry)}


def model_1_reference(jc: dict, bd: dict) -> dict:
    if jc.get("market") != "JC" or bd.get("market") != "BD":
        raise ValueError("MODEL_1 requires separate JC and BD query results")
    j, b = jc.get("label"), bd.get("label")
    signal = ("STRONG_EXCLUDE" if b == 1 else "EXCLUDE") if j == 1 else (
        "NO_EXCLUSION_SIGNAL" if j == 0 else "UNKNOWN")
    return {
        "PRIMARY_LAYER": "JC", "SECONDARY_VALIDATION_LAYER": "BD",
        "JC_layer": layer("JC", jc), "BD_layer": layer("BD", bd),
        "teacher_reference_signal": signal,
        "teacher_exclusion_reference": True if j == 1 else False if j == 0 else None,
        "bd_counterevidence": j == 1 and b == 0,
        "bd_risk_hint": b == 1 and j != 1,
        "independent_student_analysis_required": True,
    }
