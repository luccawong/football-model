import unittest
from exchange_bridge.oddspapi import OddsPapiError, build_1x2_outcome_map, match_fixture, normalize_fixture_odds

MARKETS = [{
    "marketId": 101,
    "marketLength": 3,
    "marketName": "Full Time Result",
    "sportId": 10,
    "playerProp": False,
    "handicap": 0,
    "period": "fulltime",
    "marketType": "1x2",
    "outcomes": [
        {"outcomeId": 101, "outcomeName": "1"},
        {"outcomeId": 102, "outcomeName": "X"},
        {"outcomeId": 103, "outcomeName": "2"},
    ],
}]

FIXTURE = {
    "fixtureId": "id100001",
    "participant1Name": "Cagliari",
    "participant2Name": "Lecce",
    "sportId": 10,
    "statusId": 0,
    "startTime": "2026-09-07T16:30:00.000Z",
}

ODDS = {
    **FIXTURE,
    "tournamentId": 31,
    "hasOdds": True,
    "bookmakerOdds": {
        "betfair-ex": {
            "bookmakerIsActive": True,
            "bookmakerFixtureId": "bf123",
            "fixturePath": "https://example.invalid/bf123",
            "suspended": False,
            "markets": {
                "101": {
                    "bookmakerMarketId": "1.12345",
                    "marketActive": True,
                    "outcomes": {
                        "101": {"players": {"0": {
                            "active": True, "bookmakerOutcomeId": "home",
                            "bookmakerChangedAt": "2026-09-07T12:00:00Z",
                            "changedAt": "2026-09-07T12:00:01Z",
                            "limit": 100, "price": 2.12, "mainLine": True,
                            "exchangeMeta": {"layPrice": 2.16, "liquidity": 50},
                        }}},
                        "102": {"players": {"0": {
                            "active": True, "bookmakerOutcomeId": "draw",
                            "bookmakerChangedAt": None,
                            "changedAt": "2026-09-07T12:00:01Z",
                            "limit": 80, "price": 3.20, "mainLine": True,
                            "exchangeMeta": {"layPrice": 3.25},
                        }}},
                        "103": {"players": {"0": {
                            "active": True, "bookmakerOutcomeId": "away",
                            "bookmakerChangedAt": "2026-09-07T12:00:00Z",
                            "changedAt": "2026-09-07T12:00:01Z",
                            "limit": 60, "price": 3.90, "mainLine": True,
                            "exchangeMeta": None,
                        }}},
                    },
                }
            },
        }
    },
}


class TestOddsPapiV4Bridge(unittest.TestCase):
    def test_market_map(self):
        self.assertEqual(build_1x2_outcome_map(MARKETS), {101: "home", 102: "draw", 103: "away"})

    def test_match_fixture(self):
        self.assertEqual(
            match_fixture([FIXTURE], "Cagliari", "Lecce", "2026-09-07T16:30:00Z")["fixtureId"],
            "id100001",
        )

    def test_pinned_fixture(self):
        self.assertEqual(match_fixture([FIXTURE], "x", "y", provider_fixture_id="id100001")["fixtureId"], "id100001")

    def test_normalize_preserves_exchange_meta(self):
        packet = normalize_fixture_odds(ODDS, "2993777", build_1x2_outcome_map(MARKETS))
        selections = packet["selected_bookmaker"]["selections"]
        self.assertEqual(selections["home"]["price"], 2.12)
        self.assertEqual(selections["home"]["limit"], 100)
        self.assertEqual(selections["home"]["exchangeMeta"]["layPrice"], 2.16)
        self.assertEqual(selections["home"]["bookmakerChangedAt"], "2026-09-07T12:00:00Z")
        self.assertTrue(packet["qc"]["exchange_meta_preserved_raw"])

    def test_no_fake_total_matched_or_depth(self):
        packet = normalize_fixture_odds(ODDS, "2993777", build_1x2_outcome_map(MARKETS))
        self.assertIn("total_matched", packet["unavailable_fields"])
        self.assertIn("guaranteed_multi_level_back_lay_depth", packet["unavailable_fields"])
        self.assertFalse(packet["qc"]["total_matched_available"])

    def test_bad_match(self):
        with self.assertRaises(OddsPapiError):
            match_fixture([FIXTURE], "Roma", "Milan", "2026-09-07T16:30:00Z")


if __name__ == "__main__":
    unittest.main()
