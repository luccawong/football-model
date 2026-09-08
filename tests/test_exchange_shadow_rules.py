import unittest

from gpt.exchange_shadow_rules import evaluate_shadow_rules


class TestExchangeShadowRules(unittest.TestCase):
    def test_r62_high_probability_lowest_kelly(self):
        r = evaluate_shadow_rules({
            'selection_probability': 0.64,
            'kelly_index': 0.91,
            'all_selection_kelly_indices': [0.91, 0.97, 1.02],
        })['rules']['R62']
        self.assertEqual(r['state'], 'TRIGGERED')

    def test_r63_consensus(self):
        r = evaluate_shadow_rules({
            'best_back': 2.34,
            'best_lay': 2.38,
            'wom_pct': 52,
        })['rules']['R63']
        self.assertEqual(r['state'], 'TRIGGERED')

    def test_r66_two_sd(self):
        r = evaluate_shadow_rules({
            'ou_profitability': 14,
            'ou_profitability_baseline_mean': 10,
            'ou_profitability_baseline_sd': 2,
        })['rules']['R66']
        self.assertEqual(r['state'], 'TRIGGERED')

    def test_r74_one_point_five_sd(self):
        r = evaluate_shadow_rules({
            'kelly_dispersion': 1.3,
            'kelly_dispersion_baseline_mean': 1.0,
            'kelly_dispersion_baseline_sd': 0.2,
        })['rules']['R74']
        self.assertEqual(r['state'], 'TRIGGERED')

    def test_r76_gap_proxy(self):
        self.assertEqual(evaluate_shadow_rules({'spread_ticks': 2})['rules']['R76']['state'], 'TRIGGERED')
        self.assertEqual(evaluate_shadow_rules({'spread_ticks': 1})['rules']['R76']['state'], 'NOT_TRIGGERED')

    def test_r39_volume_up_price_down(self):
        r = evaluate_shadow_rules({
            'traded_volume_timeseries': [1000, 1800],
            'price_timeseries': [2.20, 2.04],
        })['rules']['R39']
        self.assertEqual(r['state'], 'TRIGGERED')

    def test_unresolved_rules_do_not_get_invented(self):
        rules = evaluate_shadow_rules({
            'home_profit_loss_ratio': 1.0,
            'draw_profit_loss_ratio': 1.01,
            'away_profit_loss_ratio': 0.99,
            'kelly_heat_index': 0.5,
        })['rules']
        self.assertEqual(rules['R61']['state'], 'UNRESOLVED')
        self.assertEqual(rules['R75']['state'], 'UNRESOLVED')
        self.assertEqual(rules['R96']['state'], 'UNRESOLVED')
        self.assertEqual(rules['R99']['state'], 'UNRESOLVED')

    def test_shadow_never_formal(self):
        packet = evaluate_shadow_rules({})
        self.assertFalse(packet['formal_system_impact'])
        self.assertEqual(packet['integration_mode'], 'shadow_research')


if __name__ == '__main__':
    unittest.main()
