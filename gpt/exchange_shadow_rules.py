"""Betfair shadow-rule evaluator.

Evaluates the user-supplied Betfair/depth and market-game heuristics without
allowing them to alter the formal football system during the current shadow
test. Undefined source thresholds stay UNRESOLVED; missing data stays MISSING.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence
import math

SHADOW_RULE_ENGINE_VERSION = "BETFAIR-SHADOW-RULES-1.0.0"
VALID_STATES = {"TRIGGERED", "NOT_TRIGGERED", "MISSING", "UNRESOLVED", "CONFLICT"}


def _finite(x: Any) -> bool:
    try:
        return math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def _result(rule_id: str, state: str, inputs: Mapping[str, Any] | None = None, note: str = "") -> Dict[str, Any]:
    if state not in VALID_STATES:
        raise ValueError(f"invalid shadow-rule state: {state}")
    return {
        "rule_id": rule_id,
        "state": state,
        "inputs": dict(inputs or {}),
        "note": note,
    }


def _zscore(value: Any, mean: Any, sd: Any) -> float | None:
    if not (_finite(value) and _finite(mean) and _finite(sd)):
        return None
    sd_f = float(sd)
    if sd_f <= 0:
        return None
    return (float(value) - float(mean)) / sd_f


def evaluate_shadow_rules(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Evaluate all currently registered screenshot rules.

    The input mapping is intentionally explicit. No missing field is inferred
    from another concept. This protects the shadow test from post-hoc filling
    and from inventing thresholds absent from the source screenshots.
    """
    out: Dict[str, Dict[str, Any]] = {}

    # R61: source says the three P/L ratios are "close" but supplies no tolerance.
    r61_keys = ("home_profit_loss_ratio", "draw_profit_loss_ratio", "away_profit_loss_ratio")
    if all(k in data and _finite(data[k]) for k in r61_keys):
        out["R61"] = _result("R61", "UNRESOLVED", {k: data[k] for k in r61_keys}, "Source screenshot does not define how close the three profit/loss ratios must be.")
    else:
        out["R61"] = _result("R61", "MISSING", note="Need all three outcome profit/loss ratios.")

    # R62: probability >60% and the selection has the lowest Kelly index.
    p = data.get("selection_probability")
    k = data.get("kelly_index")
    all_k = data.get("all_selection_kelly_indices")
    if _finite(p) and _finite(k) and isinstance(all_k, Sequence) and not isinstance(all_k, (str, bytes)) and all(_finite(x) for x in all_k) and len(all_k) >= 2:
        triggered = float(p) > 0.60 and float(k) <= min(float(x) for x in all_k) + 1e-12
        out["R62"] = _result("R62", "TRIGGERED" if triggered else "NOT_TRIGGERED", {"selection_probability": p, "kelly_index": k, "all_selection_kelly_indices": list(all_k)})
    else:
        out["R62"] = _result("R62", "MISSING", note="Need selection probability and Kelly indices for all outcomes.")

    # R63: Back/Lay raw odds spread <0.10 and WoM 40-60%.
    back, lay, wom = data.get("best_back"), data.get("best_lay"), data.get("wom_pct")
    if _finite(back) and _finite(lay) and _finite(wom):
        spread = float(lay) - float(back)
        if spread < 0:
            out["R63"] = _result("R63", "CONFLICT", {"best_back": back, "best_lay": lay, "wom_pct": wom}, "Lay below Back is invalid for a normal snapshot.")
        else:
            triggered = spread < 0.10 and 40.0 <= float(wom) <= 60.0
            out["R63"] = _result("R63", "TRIGGERED" if triggered else "NOT_TRIGGERED", {"best_back": back, "best_lay": lay, "spread": spread, "wom_pct": wom})
    else:
        out["R63"] = _result("R63", "MISSING", note="Need best Back, best Lay and WoM.")

    # R64: >40% share is defined, but 'deep' and 'large order' absolute threshold are not.
    if _finite(data.get("deep_order_share_pct")):
        out["R64"] = _result("R64", "UNRESOLVED", {"deep_order_share_pct": data.get("deep_order_share_pct")}, "Deep-level and large-order absolute definitions are absent from source.")
    else:
        out["R64"] = _result("R64", "MISSING", note="Need deep-order share and a validated deep-level definition.")

    # R65: WoM<35% is defined; 'Lay far exceeds Back' multiplier is not.
    if _finite(data.get("wom_pct")) and _finite(data.get("back_depth")) and _finite(data.get("lay_depth")):
        out["R65"] = _result("R65", "UNRESOLVED", {"wom_pct": data.get("wom_pct"), "back_depth": data.get("back_depth"), "lay_depth": data.get("lay_depth")}, "Source does not define how much Lay depth must exceed Back depth.")
    else:
        out["R65"] = _result("R65", "MISSING", note="Need WoM and Back/Lay depth.")

    # R66: OU profitability deviation >=2 standard deviations.
    z66 = _zscore(data.get("ou_profitability"), data.get("ou_profitability_baseline_mean"), data.get("ou_profitability_baseline_sd"))
    if z66 is None:
        out["R66"] = _result("R66", "MISSING", note="Need OU profitability plus valid baseline mean and SD.")
    else:
        out["R66"] = _result("R66", "TRIGGERED" if abs(z66) >= 2.0 else "NOT_TRIGGERED", {"z": z66, "ou_profitability": data.get("ou_profitability")})

    # R67: source leaves 'high price' and 'active order' identification undefined.
    if data.get("back_ladder") is not None and data.get("back_volume_timeseries") is not None:
        out["R67"] = _result("R67", "UNRESOLVED", {"price_position": data.get("price_position")}, "High-price and active-order definitions are not specified in source.")
    else:
        out["R67"] = _result("R67", "MISSING", note="Need Back ladder and Back-volume history.")

    # R74: Kelly-difference dispersion deviation >=1.5 standard deviations.
    z74 = _zscore(data.get("kelly_dispersion"), data.get("kelly_dispersion_baseline_mean"), data.get("kelly_dispersion_baseline_sd"))
    if z74 is None:
        out["R74"] = _result("R74", "MISSING", note="Need Kelly dispersion plus valid baseline mean and SD.")
    else:
        out["R74"] = _result("R74", "TRIGGERED" if abs(z74) >= 1.5 else "NOT_TRIGGERED", {"z": z74, "kelly_dispersion": data.get("kelly_dispersion")})

    # R75: 'low Kelly heat index' has no threshold.
    if _finite(data.get("kelly_heat_index")):
        out["R75"] = _result("R75", "UNRESOLVED", {"kelly_heat_index": data.get("kelly_heat_index"), "bookmaker_payout_risk": data.get("bookmaker_payout_risk")}, "Low-heat threshold is not defined in source.")
    else:
        out["R75"] = _result("R75", "MISSING", note="Need Kelly heat index.")

    # R76: use only the documented proxy: >1 Betfair tick between best Back/Lay.
    ticks = data.get("spread_ticks")
    if isinstance(ticks, int) and ticks >= 0:
        out["R76"] = _result("R76", "TRIGGERED" if ticks > 1 else "NOT_TRIGGERED", {"spread_ticks": ticks}, "Proxy detects a price-gap/no-man's-land candidate only; it does not prove who will be consumed.")
    else:
        out["R76"] = _result("R76", "MISSING", note="Need validated Betfair spread_ticks.")

    # R77: current OddsPapi feed does not provide matched-trade side direction.
    if data.get("matched_trade_side_direction") is None or data.get("price_direction") is None:
        out["R77"] = _result("R77", "MISSING", note="Need matched-trade side direction and price direction; runner tradedVolume alone is insufficient.")
    else:
        triggered = data.get("matched_trade_side_direction") != data.get("price_direction")
        out["R77"] = _result("R77", "TRIGGERED" if triggered else "NOT_TRIGGERED", {"matched_trade_side_direction": data.get("matched_trade_side_direction"), "price_direction": data.get("price_direction")})

    # R36: >=2 contradictory independent dimensions.
    c = data.get("contradictory_dimensions")
    if isinstance(c, int) and c >= 0:
        out["R36"] = _result("R36", "TRIGGERED" if c >= 2 else "NOT_TRIGGERED", {"contradictory_dimensions": c})
    else:
        out["R36"] = _result("R36", "MISSING", note="Need count of independent contradictory dimensions.")

    # R37: subjective 'performance-like' label must be explicitly supplied, never inferred silently.
    if data.get("favorite_signal_stack_complete") is None or data.get("performance_like_flag") is None:
        out["R37"] = _result("R37", "MISSING", note="Need explicit favorite-stack and performance-like review flags.")
    else:
        trig = bool(data.get("favorite_signal_stack_complete")) and bool(data.get("performance_like_flag"))
        out["R37"] = _result("R37", "TRIGGERED" if trig else "NOT_TRIGGERED", {"favorite_signal_stack_complete": bool(data.get("favorite_signal_stack_complete")), "performance_like_flag": bool(data.get("performance_like_flag"))})

    # R38: main direction supported while opposite side has no support.
    if data.get("main_direction_support") is None or data.get("opposite_direction_support") is None:
        out["R38"] = _result("R38", "MISSING", note="Need explicit support states for main and opposite directions.")
    else:
        trig = bool(data.get("main_direction_support")) and not bool(data.get("opposite_direction_support"))
        out["R38"] = _result("R38", "TRIGGERED" if trig else "NOT_TRIGGERED", {"main_direction_support": bool(data.get("main_direction_support")), "opposite_direction_support": bool(data.get("opposite_direction_support"))})

    # R39: volume increases while odds fall across at least two pre-match snapshots.
    vols, prices = data.get("traded_volume_timeseries"), data.get("price_timeseries")
    if isinstance(vols, Sequence) and isinstance(prices, Sequence) and not isinstance(vols, (str, bytes)) and not isinstance(prices, (str, bytes)) and len(vols) >= 2 and len(prices) >= 2 and all(_finite(x) for x in vols) and all(_finite(x) for x in prices):
        trig = float(vols[-1]) > float(vols[0]) and float(prices[-1]) < float(prices[0])
        out["R39"] = _result("R39", "TRIGGERED" if trig else "NOT_TRIGGERED", {"volume_start": vols[0], "volume_end": vols[-1], "price_start": prices[0], "price_end": prices[-1]})
    else:
        out["R39"] = _result("R39", "MISSING", note="Need at least two valid pre-match runner tradedVolume and price snapshots.")

    # R58: >80% concentration + AH not adjusted. 'Control' remains only the source heuristic label.
    conc = data.get("betfair_concentration_pct")
    ah_no_adjust = data.get("asian_handicap_not_adjusted")
    if _finite(conc) and ah_no_adjust is not None:
        trig = float(conc) > 80.0 and bool(ah_no_adjust)
        out["R58"] = _result("R58", "TRIGGERED" if trig else "NOT_TRIGGERED", {"betfair_concentration_pct": conc, "asian_handicap_not_adjusted": bool(ah_no_adjust)}, "Trigger is a heuristic flag, not proof of bookmaker control.")
    else:
        out["R58"] = _result("R58", "MISSING", note="Need concentration percentage and AH-adjustment state.")

    # R59: contextual prior only; never auto-claims manipulation.
    if data.get("competition_level") is None or data.get("match_type") is None:
        out["R59"] = _result("R59", "MISSING", note="Need competition level and match type.")
    else:
        out["R59"] = _result("R59", "UNRESOLVED", {"competition_level": data.get("competition_level"), "match_type": data.get("match_type")}, "Contextual heuristic only; no calibrated probability threshold is supplied.")

    # R60: capital-control identification is undefined in source.
    if data.get("cross_bookmaker_conflict") is not None:
        out["R60"] = _result("R60", "UNRESOLVED", {"cross_bookmaker_conflict": data.get("cross_bookmaker_conflict")}, "Objective 'large capital fighting for control' threshold is not defined.")
    else:
        out["R60"] = _result("R60", "MISSING", note="Need cross-bookmaker conflict evidence.")

    # R96/R99: source references three conditions but does not provide them.
    out["R96"] = _result("R96", "UNRESOLVED", note="The three validation conditions are not present in supplied screenshots.")
    out["R99"] = _result("R99", "UNRESOLVED", note="The three validation conditions are not present in supplied screenshots.")

    return {
        "engine_version": SHADOW_RULE_ENGINE_VERSION,
        "integration_mode": "shadow_research",
        "formal_system_impact": False,
        "rules": out,
        "summary": {
            state: sum(1 for r in out.values() if r["state"] == state)
            for state in sorted(VALID_STATES)
        },
    }
