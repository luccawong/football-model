import unittest
from gpt.feature_engine import (
    normalized_entropy_1x2, ensemble_disagreement, brier_1x2, rps_1x2,
    log_loss_1x2, ah_lifecycle, probability_lifecycle, source_freshness,
    module_gate, schedule_pressure, calibration_bins
)

class TestFeatureEngine(unittest.TestCase):
    def test_entropy(self): self.assertAlmostEqual(normalized_entropy_1x2([1/3,1/3,1/3]),1.0,places=12)
    def test_scores_perfect(self):
        self.assertEqual(brier_1x2([1,0,0],0),0); self.assertEqual(rps_1x2([1,0,0],0),0); self.assertEqual(log_loss_1x2([1,0,0],0),0)
    def test_disagreement(self):
        d=ensemble_disagreement({'a':[.5,.3,.2],'b':[.4,.3,.3]}); self.assertAlmostEqual(d['mean']['home'],.45,places=12); self.assertGreater(d['range_pp']['home'],9.9)
    def test_ah_failed_upgrade(self):
        x=ah_lifecycle([{'line':-.25},{'line':-.5},{'line':-.25}]); self.assertTrue(x['failed_upgrade']); self.assertEqual(x['reversals'],1)
    def test_prob_lifecycle(self):
        x=probability_lifecycle([.4,.5,.46]); self.assertEqual(x['reversals'],1); self.assertAlmostEqual(x['net_pp'],6,places=12)
    def test_freshness(self):
        self.assertEqual(source_freshness(2,12,6)['status'],'FRESH'); self.assertEqual(source_freshness(8,12,6)['status'],'STALE_WARNING'); self.assertEqual(source_freshness(20,12,6)['status'],'STALE_BLOCK')
    def test_gate(self):
        self.assertTrue(module_gate({'x':{'status':'MISSING','critical':True}})['hard_block']); self.assertFalse(module_gate({'x':{'status':'PARTIAL','critical':True}})['hard_block'])
    def test_schedule(self):
        x=schedule_pressure(2.5,3,3000); self.assertIn('SHORT_REST_SEVERE',x['flags']); self.assertIsNone(x['probability_adjustment'])
    def test_calibration(self): self.assertLess(calibration_bins([.1,.2,.8,.9],[0,0,1,1],2)['ece'],.2)

if __name__ == '__main__': unittest.main()
