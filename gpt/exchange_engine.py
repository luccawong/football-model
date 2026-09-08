"""GPT Football Betfair Exchange evidence engine v1.1.0.

Deterministic microstructure helpers for Betfair Exchange market data.
This layer is descriptive evidence only. It never treats exchange flow as
"smart money" by default and never issues a betting recommendation.
"""
from __future__ import annotations
from typing import Any, Dict, Mapping, Sequence
import math

EXCHANGE_ENGINE_VERSION = "GPT-EXCHANGE-1.1.0"

class ExchangeInputError(ValueError):
    pass


def _validate_price(price: float) -> float:
    p = float(price)
    if not math.isfinite(p) or p <= 1.0:
        raise ExchangeInputError("Exchange prices must be finite decimal odds > 1.0.")
    return p


def _betfair_ticks() -> list[float]:
    bands = [
        (1.01, 2.0, 0.01), (2.0, 3.0, 0.02), (3.0, 4.0, 0.05),
        (4.0, 6.0, 0.10), (6.0, 10.0, 0.20), (10.0, 20.0, 0.50),
        (20.0, 30.0, 1.0), (30.0, 50.0, 2.0), (50.0, 100.0, 5.0),
        (100.0, 1000.0, 10.0),
    ]
    out: list[float] = []
    for lo, hi, step in bands:
        x = lo
        while x < hi - 1e-9:
            out.append(round(x, 2))
            x += step
    out.append(1000.0)
    return out

_BETFAIR_TICKS = _betfair_ticks()
_BETFAIR_TICK_INDEX = {round(v, 2): i for i, v in enumerate(_BETFAIR_TICKS)}


def tick_distance(price_a: float, price_b: float) -> int:
    a, b = round(_validate_price(price_a), 2), round(_validate_price(price_b), 2)
    if a not in _BETFAIR_TICK_INDEX or b not in _BETFAIR_TICK_INDEX:
        raise ExchangeInputError("Price is not on the Betfair tick ladder.")
    return abs(_BETFAIR_TICK_INDEX[a] - _BETFAIR_TICK_INDEX[b])


def book_percentage(prices: Sequence[float]) -> float:
    if not prices:
        raise ExchangeInputError("At least one price is required.")
    return float(sum(1.0 / _validate_price(p) for p in prices))


def normalized_implied_probabilities(prices: Mapping[str, float]) -> Dict[str, float]:
    if not prices:
        raise ExchangeInputError("At least one runner price is required.")
    raw = {str(k): 1.0 / _validate_price(v) for k, v in prices.items()}
    s = sum(raw.values())
    return {k: v / s for k, v in raw.items()}


def runner_spread(best_back: float, best_lay: float) -> Dict[str, float | int]:
    back, lay = _validate_price(best_back), _validate_price(best_lay)
    if lay < back:
        raise ExchangeInputError("Best lay price cannot be below best back price in a valid snapshot.")
    back_p, lay_p = 1.0 / back, 1.0 / lay
    return {
        "best_back": back,
        "best_lay": lay,
        "odds_spread": lay - back,
        "spread_ticks": tick_distance(back, lay),
        "back_implied_probability": back_p,
        "lay_implied_probability": lay_p,
        "mid_implied_probability": (back_p + lay_p) / 2.0,
        "probability_spread_pp": (back_p - lay_p) * 100.0,
    }


def order_book_imbalance(back_sizes: Sequence[float], lay_sizes: Sequence[float]) -> Dict[str, float]:
    b = [float(x) for x in back_sizes]
    l = [float(x) for x in lay_sizes]
    if any((not math.isfinite(x) or x < 0) for x in b + l):
        raise ExchangeInputError("Order-book sizes must be finite and non-negative.")
    back_depth, lay_depth = sum(b), sum(l)
    total = back_depth + lay_depth
    imbalance = 0.0 if total == 0 else (back_depth - lay_depth) / total
    return {
        "back_depth": back_depth,
        "lay_depth": lay_depth,
        "depth_total": total,
        "imbalance": imbalance,
        "note": "Descriptive liquidity imbalance only; do not infer informed direction without validation.",
    }


def traded_volume_velocity(points: Sequence[Mapping[str, float]]) -> Dict[str, float]:
    if len(points) < 2:
        raise ExchangeInputError("At least two volume points are required.")
    pts = [(float(x["t"]), float(x["total_matched"])) for x in points]
    if any(not math.isfinite(t) or not math.isfinite(v) or v < 0 for t, v in pts):
        raise ExchangeInputError("Invalid volume time series.")
    if any(pts[i+1][0] <= pts[i][0] for i in range(len(pts)-1)):
        raise ExchangeInputError("Timestamps must be strictly increasing.")
    dt_min = (pts[-1][0] - pts[0][0]) / 60.0
    delta = pts[-1][1] - pts[0][1]
    return {"delta_matched": delta, "elapsed_minutes": dt_min, "matched_per_minute": delta / dt_min}


def price_velocity(points: Sequence[Mapping[str, float]]) -> Dict[str, float]:
    if len(points) < 2:
        raise ExchangeInputError("At least two price points are required.")
    pts = [(float(x["t"]), _validate_price(x["price"])) for x in points]
    if any(pts[i+1][0] <= pts[i][0] for i in range(len(pts)-1)):
        raise ExchangeInputError("Timestamps must be strictly increasing.")
    dt_min = (pts[-1][0] - pts[0][0]) / 60.0
    p0, p1 = 1.0 / pts[0][1], 1.0 / pts[-1][1]
    return {
        "opening_price": pts[0][1],
        "current_price": pts[-1][1],
        "implied_probability_change_pp": (p1 - p0) * 100.0,
        "elapsed_minutes": dt_min,
        "implied_probability_pp_per_minute": ((p1 - p0) * 100.0) / dt_min,
    }


def exchange_vs_bookmaker_pp(exchange_probs: Mapping[str, float], bookmaker_probs: Mapping[str, float]) -> Dict[str, float]:
    keys = set(exchange_probs) & set(bookmaker_probs)
    if not keys:
        raise ExchangeInputError("No common selections between exchange and bookmaker probabilities.")
    out: Dict[str, float] = {}
    for k in sorted(keys):
        e, b = float(exchange_probs[k]), float(bookmaker_probs[k])
        if not (0 <= e <= 1 and 0 <= b <= 1):
            raise ExchangeInputError("Probabilities must lie in [0,1].")
        out[k] = (e - b) * 100.0
    return out


def market_microstructure_snapshot(runners: Mapping[str, Mapping[str, Any]], market_total_matched: float | None = None) -> Dict[str, Any]:
    if not runners:
        raise ExchangeInputError("At least one runner is required.")
    per_runner: Dict[str, Any] = {}
    back_prices: Dict[str, float] = {}
    lay_prices: Dict[str, float] = {}
    mid_prices: Dict[str, float] = {}
    for name, r in runners.items():
        back = _validate_price(r["best_back"])
        lay = _validate_price(r["best_lay"])
        spread = runner_spread(back, lay)
        imbalance = order_book_imbalance(r.get("back_sizes", []), r.get("lay_sizes", []))
        per_runner[str(name)] = {"spread": spread, "depth": imbalance, "last_price_traded": r.get("last_price_traded")}
        back_prices[str(name)] = back
        lay_prices[str(name)] = lay
        mid_p = spread["mid_implied_probability"]
        mid_prices[str(name)] = 1.0 / float(mid_p)
    mtm = None if market_total_matched is None else float(market_total_matched)
    if mtm is not None and (not math.isfinite(mtm) or mtm < 0):
        raise ExchangeInputError("market_total_matched must be finite and non-negative.")
    return {
        "engine_version": EXCHANGE_ENGINE_VERSION,
        "runners": per_runner,
        "back_book_percentage": book_percentage(list(back_prices.values())),
        "lay_book_percentage": book_percentage(list(lay_prices.values())),
        "mid_probabilities": normalized_implied_probabilities(mid_prices),
        "market_total_matched": mtm,
        "decision_rule": "Exchange microstructure is evidence, not an automatic smart-money signal or ticket.",
    }
