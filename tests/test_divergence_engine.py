from gpt.divergence_engine import assess_football_divergence


def test_low_attraction_leading_underdog_defense_reaches_a_information_grade():
    result = assess_football_divergence(
        mainstream_rows=[(0.58, 0.25, 0.17), (0.57, 0.26, 0.17)],
        secondary_rows=[(0.54, 0.25, 0.21), (0.53, 0.26, 0.21)],
        target="AWAY",
        attraction_score=25,
        persistence_minutes=45,
        independent_clusters=2,
        lead_minutes=35,
        mainstream_followed=True,
        cross_market_confirmations=1,
        frozen_at="2026-09-08T20:00:00+08:00",
    )
    assert result["magnitude_pp"] >= 4.0 - 1e-9
    assert result["uds_unnatural_defensive_signal"] is True
    assert result["lead_lag"] == "LEADING_CONFIRMED"
    assert result["information_grade"] == "A"
    assert result["probability_adjustment"] is None
    assert result["ticket_grade"] is None


def test_copied_feed_is_noise_even_with_apparent_large_divergence():
    result = assess_football_divergence(
        mainstream_rows=[(0.60, 0.24, 0.16)],
        secondary_rows=[(0.54, 0.24, 0.22)],
        target="AWAY",
        attraction_score=20,
        persistence_minutes=60,
        independent_clusters=3,
        lead_minutes=30,
        mainstream_followed=True,
        cross_market_confirmations=2,
        copied_feed=True,
    )
    assert result["uds_unnatural_defensive_signal"] is False
    assert result["information_grade"] == "NOISE"


def test_favorite_nonwin_combines_draw_and_underdog():
    result = assess_football_divergence(
        mainstream_rows=[(0.62, 0.23, 0.15)],
        secondary_rows=[(0.57, 0.25, 0.18)],
        target="FAVORITE_NONWIN",
        favorite_side="HOME",
        attraction_score=35,
        persistence_minutes=25,
        independent_clusters=2,
        cross_market_confirmations=1,
    )
    assert round(result["mainstream_target_probability"], 6) == 0.38
    assert round(result["secondary_target_probability"], 6) == 0.43
    assert round(result["magnitude_pp"], 6) == 5.0
