import unittest
from exchange_bridge.oddspapi import OddsPapiError, build_1x2_outcome_map, match_fixture, normalize_fixture_odds

MARKETS = [{"marketId":101,"marketLength":3,"sportId":10,"playerProp":False,"handicap":0,"period":"fulltime","marketType":"1x2","outcomes":[{"outcomeId":141,"outcomeName":"1"},{"outcomeId":143,"outcomeName":"X"},{"outcomeId":142,"outcomeName":"2"}]}]
FIXTURE = {"fixtureId":"id100001","startTime":1788798600,"participants":{"participant1Name":"Cagliari","participant2Name":"Lecce"}}
ODDS = {**FIXTURE,"sport":{"sportId":10,"sportName":"Soccer"},"tournament":{"tournamentName":"Serie A"},"bookmakers":{"betfair":{"hasOdds":True,"staleOdds":False,"suspended":False,"updatedAt":"2026-09-07T12:00:00Z"}},"odds":{"betfair":{"a":{"bookmaker":"betfair","outcomeId":141,"price":2.12,"active":True,"marketActive":True,"mainLine":True,"marketId":101,"changedAt":1002,"bookmakerChangedAt":1000,"limit":100,"meta":{"back":[{"price":2.12,"size":50},{"price":2.10,"size":80}],"lay":[{"price":2.16,"size":40},{"price":2.18,"size":70}]}},"b":{"bookmaker":"betfair","outcomeId":143,"price":3.20,"active":True,"marketActive":True,"mainLine":True,"marketId":101,"changedAt":1002,"meta":{"back":[{"price":3.20,"size":30}],"lay":[{"price":3.25,"size":25}]}},"c":{"bookmaker":"betfair","outcomeId":142,"price":3.90,"active":True,"marketActive":True,"mainLine":True,"marketId":101,"changedAt":1002,"meta":{"back":[{"price":3.90,"size":20}],"lay":[{"price":4.00,"size":15}]}}}}}

class TestOddsPapiBridge(unittest.TestCase):
    def test_market_map(self): self.assertEqual(build_1x2_outcome_map(MARKETS), {141:"home",143:"draw",142:"away"})
    def test_match_fixture(self): self.assertEqual(match_fixture([FIXTURE],"Cagliari","Lecce",1788798600)["fixtureId"],"id100001")
    def test_pinned_fixture(self): self.assertEqual(match_fixture([FIXTURE],"x","y",provider_fixture_id="id100001")["fixtureId"],"id100001")
    def test_normalize_orderbook(self):
        p=normalize_fixture_odds(ODDS,"2993777",build_1x2_outcome_map(MARKETS)); s=p["selected_bookmaker"]["selections"]
        self.assertEqual(s["home"]["back"]["price"],2.12); self.assertEqual(s["home"]["lay"]["price"],2.16); self.assertEqual(s["home"]["back"]["size"],50.0); self.assertEqual(s["home"]["limit"],100); self.assertTrue(p["qc"]["order_book_meta_preserved"])
    def test_no_total_matched_fabrication(self):
        p=normalize_fixture_odds(ODDS,"2993777",build_1x2_outcome_map(MARKETS)); self.assertIn("total_matched",p["unavailable_fields"])
    def test_bad_match(self):
        with self.assertRaises(OddsPapiError): match_fixture([FIXTURE],"Roma","Milan",1788798600)

if __name__ == '__main__': unittest.main()
