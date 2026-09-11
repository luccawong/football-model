from __future__ import annotations

from typing import Any, Mapping

from gpt.quant_core import score_grid, correct_score_probabilities


def automatic_top3(quant_packet: Mapping[str, Any], company: str) -> dict[str, Any]:
    reconstruction = quant_packet.get("reconstruction", {})
    if company not in reconstruction:
        return {"status": "MISSING", "reason": "NO_RECONSTRUCTION", "top3": []}
    rec = reconstruction[company]
    grid = score_grid(float(rec["lambda_home"]), float(rec["lambda_away"]), float(rec["rho"]))
    rows = correct_score_probabilities(grid, 10)
    return {"status": "MARKET_RECONSTRUCTION", "top3": rows[:3], "top10": rows}
