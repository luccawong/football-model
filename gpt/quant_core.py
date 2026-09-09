"""GPT Football Quant Engine v0.1.0.

Deterministic mathematical evidence layer for GPT-assisted football analysis.
This module does not issue betting recommendations.
"""
from __future__ import annotations

from math import exp, factorial, isfinite
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np
from scipy.optimize import brentq, least_squares

ENGINE_VERSION = "GPT-QUANT-0.1.0"


class QuantInputError(ValueError):
    """Raised when supplied odds/lines cannot be safely interpreted."""


def _validate_decimal_odds(odds: Sequence[float], expected: int | None = None) -> np.ndarray:
    arr = np.asarray(odds, dtype=float)
    if expected is not None and len(arr) != expected:
        raise QuantInputError(f"Expected {expected} odds, got {len(arr)}.")
    if len(arr) < 2:
        raise QuantInputError("At least two prices are required.")
    if not np.all(np.isfinite(arr)) or np.any(arr <= 1.0):
        raise QuantInputError("Decimal odds must be finite and strictly greater than 1.0.")
    return arr


def raw_implied_probabilities(decimal_odds: Sequence[float]) -> np.ndarray:
    odds = _validate_decimal_odds(decimal_odds)
    return 1.0 / odds


def devig_multiplicative(decimal_odds: Sequence[float]) -> np.ndarray:
    q = raw_implied_probabilities(decimal_odds)
    return q / q.sum()


def devig_power(decimal_odds: Sequence[float]) -> np.ndarray:
    """Power de-vig: find k such that sum(q_i ** k) == 1."""
    q = raw_implied_probabilities(decimal_odds)

    def f(k: float) -> float:
        return float(np.power(q, k).sum() - 1.0)

    lo, hi = 0.01, 20.0
    if f(lo) * f(hi) > 0:
        raise QuantInputError("Power de-vig root could not be bracketed.")
    k = brentq(f, lo, hi)
    p = np.power(q, k)
    return p / p.sum()


def devig_shin(decimal_odds: Sequence[float]) -> np.ndarray:
    """Shin insider-trading de-vig probabilities."""
    q = raw_implied_probabilities(decimal_odds)
    book = float(q.sum())

    def transformed(z: float) -> np.ndarray:
        if z >= 1.0:
            z = 1.0 - 1e-12
        rad = z * z + 4.0 * (1.0 - z) * (q * q / book)
        return (np.sqrt(rad) - z) / (2.0 * (1.0 - z))

    def f(z: float) -> float:
        return float(transformed(z).sum() - 1.0)

    f0, f1 = f(0.0), f(1.0 - 1e-10)
    if f0 == 0:
        p = transformed(0.0)
    elif f0 * f1 > 0:
        raise QuantInputError("Shin de-vig has no admissible root for this snapshot.")
    else:
        z = brentq(f, 0.0, 1.0 - 1e-10)
        p = transformed(z)
    return p / p.sum()


DEVIG_METHODS = {
    "multiplicative": devig_multiplicative,
    "power": devig_power,
    "shin": devig_shin,
}


def devig(decimal_odds: Sequence[float], method: str = "power") -> np.ndarray:
    try:
        fn = DEVIG_METHODS[method]
    except KeyError as exc:
        raise QuantInputError(f"Unknown de-vig method: {method}") from exc
    return fn(decimal_odds)


def _poisson_pmf(k: int, lam: float) -> float:
    if k < 0 or lam <= 0 or not isfinite(lam):
        raise QuantInputError("Poisson lambda must be finite and > 0.")
    return exp(-lam) * (lam ** k) / factorial(k)


def dixon_coles_tau(h: int, a: int, lh: float, la: float, rho: float) -> float:
    if h == 0 and a == 0:
        return 1.0 - lh * la * rho
    if h == 0 and a == 1:
        return 1.0 + lh * rho
    if h == 1 and a == 0:
        return 1.0 + la * rho
    if h == 1 and a == 1:
        return 1.0 - rho
    return 1.0


def score_grid(lambda_home: float, lambda_away: float, rho: float = 0.0, max_goals: int = 12, normalize: bool = True) -> np.ndarray:
    if lambda_home <= 0 or lambda_away <= 0:
        raise QuantInputError("Goal intensities must be > 0.")
    if not (-0.5 < rho < 0.5):
        raise QuantInputError("rho is outside safety range (-0.5, 0.5).")
    if max_goals < 6:
        raise QuantInputError("max_goals must be >= 6.")
    hp = np.array([_poisson_pmf(i, lambda_home) for i in range(max_goals + 1)])
    ap = np.array([_poisson_pmf(j, lambda_away) for j in range(max_goals + 1)])
    grid = np.outer(hp, ap)
    for i in (0, 1):
        for j in (0, 1):
            grid[i, j] *= dixon_coles_tau(i, j, lambda_home, lambda_away, rho)
    if np.any(grid < 0):
        raise QuantInputError("Dixon-Coles parameters produced negative cell probability.")
    if normalize:
        s = float(grid.sum())
        if s <= 0:
            raise QuantInputError("Score grid has zero mass.")
        grid = grid / s
    return grid


def probabilities_1x2(grid: np.ndarray) -> Dict[str, float]:
    return {
        "home": float(np.tril(grid, k=-1).sum()),
        "draw": float(np.trace(grid)),
        "away": float(np.triu(grid, k=1).sum()),
    }


def correct_score_probabilities(grid: np.ndarray, top_n: int = 10) -> List[Dict[str, float]]:
    cells = [(float(grid[h, a]), h, a) for h in range(grid.shape[0]) for a in range(grid.shape[1])]
    cells.sort(reverse=True)
    return [{"score": f"{h}-{a}", "probability": p} for p, h, a in cells[:top_n]]


def _split_quarter_line(line: float) -> Tuple[float, float]:
    q = round(line * 4) / 4
    if abs(q - line) > 1e-8:
        raise QuantInputError("Asian line must be in quarter-goal increments.")
    quarter = int(round(q * 4))
    if quarter % 2 == 0:
        return q, q
    return (quarter - 1) / 4, (quarter + 1) / 4


def _leg_result(value: float, eps: float = 1e-10) -> int:
    if value > eps:
        return 1
    if value < -eps:
        return -1
    return 0


_RESULT_KEY = {1.0: "full_win", 0.5: "half_win", 0.0: "push", -0.5: "half_loss", -1.0: "full_loss"}


def asian_handicap_settlement(grid: np.ndarray, home_handicap: float) -> Dict[str, float]:
    """Settlement probabilities when backing HOME at supplied AH."""
    l1, l2 = _split_quarter_line(home_handicap)
    out = {k: 0.0 for k in _RESULT_KEY.values()}
    for h in range(grid.shape[0]):
        for a in range(grid.shape[1]):
            margin = h - a
            payoff = (_leg_result(margin + l1) + _leg_result(margin + l2)) / 2.0
            out[_RESULT_KEY[payoff]] += float(grid[h, a])
    return out


def total_settlement(grid: np.ndarray, line: float, side: str = "over") -> Dict[str, float]:
    side = side.lower()
    if side not in {"over", "under"}:
        raise QuantInputError("side must be 'over' or 'under'.")
    l1, l2 = _split_quarter_line(line)
    out = {k: 0.0 for k in _RESULT_KEY.values()}
    sign = 1.0 if side == "over" else -1.0
    for h in range(grid.shape[0]):
        for a in range(grid.shape[1]):
            total = h + a
            payoff = (_leg_result(sign * (total - l1)) + _leg_result(sign * (total - l2))) / 2.0
            out[_RESULT_KEY[payoff]] += float(grid[h, a])
    return out


def win_equivalent_probability(settlement: Mapping[str, float]) -> float:
    """Even-price probability-equivalent payoff for fitting/comparison."""
    return (
        float(settlement["full_win"])
        + 0.5 * float(settlement["half_win"])
        + 0.5 * float(settlement["push"])
        + 0.25 * float(settlement["half_loss"])
    )


def reconstruct_market_goal_parameters(target_1x2: Mapping[str, float], ou_line: float, target_over_probability: float, max_goals: int = 12, initial: Tuple[float, float, float] = (1.5, 1.1, -0.05)) -> Dict[str, float]:
    """Fit lambda_home, lambda_away, rho from 1X2 + one O/U snapshot."""
    th, td, ta = (float(target_1x2[k]) for k in ("home", "draw", "away"))
    to = float(target_over_probability)
    if abs((th + td + ta) - 1.0) > 1e-6:
        raise QuantInputError("Target 1X2 probabilities must sum to one.")
    if not (0 < to < 1):
        raise QuantInputError("Target Over probability must lie in (0,1).")

    def residuals(x: np.ndarray) -> np.ndarray:
        lh, la, rho = map(float, x)
        try:
            g = score_grid(lh, la, rho, max_goals=max_goals)
            p = probabilities_1x2(g)
            over_equiv = win_equivalent_probability(total_settlement(g, ou_line, "over"))
            return np.array([p["home"] - th, p["draw"] - td, over_equiv - to])
        except QuantInputError:
            return np.array([10.0, 10.0, 10.0])

    fit = least_squares(residuals, np.asarray(initial, dtype=float), bounds=([0.05, 0.05, -0.25], [5.5, 5.5, 0.25]), xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=3000)
    lh, la, rho = map(float, fit.x)
    g = score_grid(lh, la, rho, max_goals=max_goals)
    p = probabilities_1x2(g)
    residual = residuals(fit.x)
    return {
        "lambda_home": lh, "lambda_away": la, "lambda_total": lh + la, "rho": rho,
        "fit_cost": float(fit.cost), "max_abs_residual": float(np.max(np.abs(residual))),
        "fitted_home": p["home"], "fitted_draw": p["draw"], "fitted_away": p["away"],
        "fitted_over_equivalent": win_equivalent_probability(total_settlement(g, ou_line, "over")),
        "success": bool(fit.success),
    }


def _binary_devig(over_odds: float, under_odds: float) -> Dict[str, float]:
    p = devig_multiplicative([over_odds, under_odds])
    return {"over": float(p[0]), "under": float(p[1])}


def _company_divergence(company_probs: Mapping[str, Mapping[str, float]], anchor: str = "Pinnacle") -> Dict[str, Dict[str, float]]:
    if anchor not in company_probs:
        return {}
    a = company_probs[anchor]
    return {
        name: {
            "vs_anchor_home_pp": 100.0 * (p["home"] - a["home"]),
            "vs_anchor_draw_pp": 100.0 * (p["draw"] - a["draw"]),
            "vs_anchor_away_pp": 100.0 * (p["away"] - a["away"]),
        }
        for name, p in company_probs.items() if name != anchor
    }


def build_quant_packet(payload: Mapping[str, Any], config: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Build a deterministic, JSON-serializable Quant Packet."""
    cfg = dict(config or {})
    method = cfg.get("one_x_two_devig_method", "power")
    max_goals = int(cfg.get("max_goals", 12))
    anchor = cfg.get("divergence_anchor", "Pinnacle")
    companies = payload.get("companies")
    if not isinstance(companies, Mapping) or not companies:
        raise QuantInputError("payload.companies is required.")

    packet: Dict[str, Any] = {
        "engine_version": ENGINE_VERSION,
        "match_id": str(payload.get("match_id", "")),
        "snapshot_time": payload.get("snapshot_time"),
        "input_policy": {
            "same_time_slice_required": True,
            "one_x_two_devig_method": method,
            "dynamic_ou_primary_companies": cfg.get("dynamic_ou_primary_companies", ["Macau", "Pinnacle", "Bet365"]),
            "base_2_5_companies": cfg.get("base_2_5_companies", ["WilliamHill", "Ladbrokes"]),
        },
        "companies": {}, "company_divergence_pp": {}, "reconstruction": {},
        "status": "OK", "warnings": [],
    }
    selected_probs: Dict[str, Dict[str, float]] = {}

    for name, raw in companies.items():
        item: Dict[str, Any] = {}
        if raw.get("one_x_two") is not None:
            prices = [float(x) for x in raw["one_x_two"]]
            methods: Dict[str, Any] = {}
            for m in ("multiplicative", "power", "shin"):
                try:
                    p = devig(prices, m)
                    methods[m] = {"home": float(p[0]), "draw": float(p[1]), "away": float(p[2])}
                except QuantInputError as exc:
                    methods[m] = {"error": str(exc)}
            item["one_x_two_decimal"] = prices
            item["devig"] = methods
            selected = methods.get(method, {})
            if selected and "error" not in selected:
                selected_probs[name] = dict(selected)

        ou = raw.get("ou")
        if isinstance(ou, Mapping):
            item["ou"] = {
                "line": float(ou["line"]), "over_decimal": float(ou["over"]), "under_decimal": float(ou["under"]),
                "role": ou.get("role", "dynamic"), "devig": _binary_devig(float(ou["over"]), float(ou["under"])),
            }
        packet["companies"][name] = item

    packet["company_divergence_pp"] = _company_divergence(selected_probs, anchor)

    for name, item in packet["companies"].items():
        if name not in selected_probs or "ou" not in item:
            continue
        try:
            ou = item["ou"]
            rec = reconstruct_market_goal_parameters(selected_probs[name], float(ou["line"]), float(ou["devig"]["over"]), max_goals=max_goals)
            g = score_grid(rec["lambda_home"], rec["lambda_away"], rec["rho"], max_goals=max_goals)
            rec["correct_score_top10"] = correct_score_probabilities(g, 10)
            rec["market_1x2"] = probabilities_1x2(g)
            rec["ou"] = {str(line): {"over": total_settlement(g, float(line), "over"), "under": total_settlement(g, float(line), "under")} for line in cfg.get("report_ou_lines", [2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5])}
            rec["home_asian_handicap"] = {str(line): asian_handicap_settlement(g, float(line)) for line in cfg.get("report_ah_lines", [0.0, -0.25, -0.5, -0.75, -1.0, -1.25, -1.5])}
            packet["reconstruction"][name] = rec
            if rec["max_abs_residual"] > float(cfg.get("max_fit_residual", 0.015)):
                packet["warnings"].append(f"{name}: reconstruction residual {rec['max_abs_residual']:.4f} exceeds threshold.")
        except Exception as exc:
            packet["warnings"].append(f"{name}: reconstruction failed: {exc}")

    checks = []
    for name, p in selected_probs.items():
        checks.append((f"{name}.1x2_sum", abs(sum(p.values()) - 1.0) < 1e-8))
    for name, rec in packet["reconstruction"].items():
        try:
            g = score_grid(rec["lambda_home"], rec["lambda_away"], rec["rho"], max_goals=max_goals)
            checks.append((f"{name}.grid_sum", abs(float(g.sum()) - 1.0) < 1e-8))
            px = probabilities_1x2(g)
            checks.append((f"{name}.draw_diagonal", abs(px["draw"] - float(np.trace(g))) < 1e-12))
            ah = asian_handicap_settlement(g, -0.5)
            checks.append((f"{name}.ah_m05_equals_homewin", abs(ah["full_win"] - px["home"]) < 1e-10))
        except Exception:
            checks.append((f"{name}.grid_integrity", False))

    packet["validation"] = {name: ok for name, ok in checks}
    if checks and not all(ok for _, ok in checks):
        packet["status"] = "FAIL"
    elif not packet["reconstruction"]:
        packet["status"] = "PARTIAL"
        packet["warnings"].append("No company had both usable 1X2 and O/U prices; lambda reconstruction unavailable.")
    return packet
