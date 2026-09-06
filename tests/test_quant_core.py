import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gpt"))

from quant_core import (
    asian_handicap_settlement,
    build_quant_packet,
    devig_multiplicative,
    devig_power,
    devig_shin,
    probabilities_1x2,
    reconstruct_market_goal_parameters,
    score_grid,
    total_settlement,
)


class TestQuantCore(unittest.TestCase):
    def test_devig_sums_to_one(self):
        odds = [1.80, 3.80, 4.60]
        for fn in (devig_multiplicative, devig_power, devig_shin):
            p = fn(odds)
            self.assertAlmostEqual(float(sum(p)), 1.0, places=10)
            self.assertTrue(all(0 < x < 1 for x in p))

    def test_score_grid_normalized(self):
        g = score_grid(1.7, 1.1, -0.05)
        self.assertAlmostEqual(float(g.sum()), 1.0, places=10)

    def test_symmetric_lambdas_symmetric_outcomes(self):
        g = score_grid(1.4, 1.4, -0.05)
        p = probabilities_1x2(g)
        self.assertAlmostEqual(p["home"], p["away"], places=10)

    def test_draw_is_diagonal(self):
        g = score_grid(1.8, 0.9, -0.04)
        p = probabilities_1x2(g)
        self.assertAlmostEqual(p["draw"], float(g.trace()), places=12)

    def test_home_minus_half_equals_home_win_probability(self):
        g = score_grid(1.8, 0.9, -0.04)
        p = probabilities_1x2(g)
        ah = asian_handicap_settlement(g, -0.5)
        self.assertAlmostEqual(ah["full_win"], p["home"], places=10)
        self.assertAlmostEqual(sum(ah.values()), 1.0, places=10)

    def test_over_probability_monotonicity(self):
        g = score_grid(1.8, 1.2, -0.04)
        o25 = total_settlement(g, 2.5, "over")["full_win"]
        o35 = total_settlement(g, 3.5, "over")["full_win"]
        self.assertGreaterEqual(o25, o35)

    def test_quarter_settlement_sums_to_one(self):
        g = score_grid(1.8, 1.2, -0.04)
        for result in (asian_handicap_settlement(g, -0.75), total_settlement(g, 2.75, "over"), total_settlement(g, 2.25, "under")):
            self.assertAlmostEqual(sum(result.values()), 1.0, places=10)

    def test_market_reconstruction_on_synthetic_target(self):
        source = score_grid(1.65, 1.05, -0.06)
        target = probabilities_1x2(source)
        over = total_settlement(source, 2.5, "over")["full_win"]
        rec = reconstruct_market_goal_parameters(target, 2.5, over)
        self.assertTrue(rec["success"])
        self.assertLess(rec["max_abs_residual"], 1e-5)
        self.assertAlmostEqual(rec["lambda_home"], 1.65, places=2)
        self.assertAlmostEqual(rec["lambda_away"], 1.05, places=2)

    def test_packet_integrity(self):
        payload = {
            "match_id": "T-001",
            "snapshot_time": "2026-09-07T18:42:00+08:00",
            "companies": {
                "Pinnacle": {"one_x_two": [1.80, 3.80, 4.60], "ou": {"line": 2.5, "over": 1.88, "under": 2.00, "role": "dynamic"}},
                "WilliamHill": {"one_x_two": [1.76, 3.70, 4.80], "ou": {"line": 2.5, "over": 1.83, "under": 1.95, "role": "base_2_5"}},
            },
        }
        cfg = json.loads((ROOT / "config" / "quant_config.json").read_text())
        packet = build_quant_packet(payload, cfg)
        self.assertIn(packet["status"], {"OK", "PARTIAL"})
        self.assertIn("Pinnacle", packet["companies"])
        self.assertIn("WilliamHill", packet["company_divergence_pp"])


if __name__ == "__main__":
    unittest.main()
