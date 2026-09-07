import unittest
from gpt.exchange_engine import (
    tick_distance, book_percentage, normalized_implied_probabilities,
    runner_spread, order_book_imbalance, traded_volume_velocity,
    price_velocity, exchange_vs_bookmaker_pp, market_microstructure_snapshot,
)

class TestExchangeEngine(unittest.TestCase):
    def test_tick_distance(self): self.assertEqual(tick_distance(2.0,2.04),2)
    def test_book(self): self.assertAlmostEqual(book_percentage([2.0,4.0,4.0]),1.0,places=12)
    def test_probs(self): self.assertAlmostEqual(sum(normalized_implied_probabilities({'h':2,'d':4,'a':4}).values()),1.0,places=12)
    def test_spread(self): self.assertEqual(runner_spread(2.0,2.04)['spread_ticks'],2)
    def test_imbalance(self): self.assertAlmostEqual(order_book_imbalance([100,50],[50,50])['imbalance'],0.2,places=12)
    def test_volume_velocity(self): self.assertAlmostEqual(traded_volume_velocity([{'t':0,'total_matched':100},{'t':120,'total_matched':220}])['matched_per_minute'],60.0,places=12)
    def test_price_velocity(self): self.assertGreater(price_velocity([{'t':0,'price':2.2},{'t':60,'price':2.0}])['implied_probability_pp_per_minute'],0)
    def test_exchange_vs_bookmaker(self): self.assertAlmostEqual(exchange_vs_bookmaker_pp({'h':.5},{'h':.48})['h'],2.0,places=12)
    def test_packet(self):
        x=market_microstructure_snapshot({'h':{'best_back':2.0,'best_lay':2.04,'back_sizes':[100,50],'lay_sizes':[60,40]},'d':{'best_back':4.0,'best_lay':4.1,'back_sizes':[40],'lay_sizes':[40]},'a':{'best_back':4.0,'best_lay':4.1,'back_sizes':[50],'lay_sizes':[60]}},10000)
        self.assertAlmostEqual(sum(x['mid_probabilities'].values()),1.0,places=12)
        self.assertEqual(x['engine_version'],'GPT-EXCHANGE-1.0.0')

if __name__=='__main__': unittest.main()
