import unittest
from exchange_bridge.the_odds_api import match_event, normalize_event, OddsApiError

EVENT = {
    "id":"evt1","sport_key":"soccer_italy_serie_a","sport_title":"Serie A","commence_time":"2026-09-07T16:30:00Z",
    "home_team":"Cagliari","away_team":"Lecce","bookmakers":[{"key":"betfair_ex_uk","title":"Betfair","last_update":"2026-09-07T12:00:00Z","markets":[
        {"key":"h2h","last_update":"2026-09-07T12:00:00Z","outcomes":[{"name":"Cagliari","price":2.12,"bet_limit":100},{"name":"Draw","price":3.20,"bet_limit":80},{"name":"Lecce","price":3.90,"bet_limit":60}]},
        {"key":"h2h_lay","last_update":"2026-09-07T12:00:00Z","outcomes":[{"name":"Cagliari","price":2.16,"bet_limit":90},{"name":"Draw","price":3.25,"bet_limit":70},{"name":"Lecce","price":4.00,"bet_limit":50}]}
    ]}]
}

class TestExchangeBridge(unittest.TestCase):
    def test_match_event(self): self.assertEqual(match_event([EVENT],"Cagliari","Lecce","2026-09-07T16:30:00Z")["id"],"evt1")
    def test_provider_id(self): self.assertEqual(match_event([EVENT],"x","y",provider_event_id="evt1")["id"],"evt1")
    def test_normalize(self):
        p=normalize_event(EVENT,"2993777",observed_at="2026-09-07T12:00:01Z"); s=p["selected_bookmaker"]["selections"]
        self.assertEqual(s["home"]["back"]["price"],2.12); self.assertEqual(s["home"]["lay"]["price"],2.16); self.assertEqual(s["draw"]["back"]["bet_limit"],80)
    def test_no_fake_volume(self):
        p=normalize_event(EVENT,"2993777"); self.assertIn("total_matched",p["unavailable_fields"]); self.assertTrue(p["qc"]["bet_limit_is_not_matched_volume"])
    def test_bad_match(self):
        with self.assertRaises(OddsApiError): match_event([EVENT],"Roma","Milan","2026-09-07T16:30:00Z")

if __name__ == "__main__": unittest.main()
