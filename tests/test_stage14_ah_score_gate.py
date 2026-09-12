from gpt.stage14_bayesian import select_direction_consistent_top3


def _predictive(scores):
    return {
        "status": "BAYESIAN_POSTERIOR_PREDICTIVE",
        "top10": [
            {"score": score, "probability": probability, "robustness_top3_frequency": 0.5}
            for score, probability in scores
        ],
    }


def test_favorite_minus_one_rejects_push_scores_from_final_top3():
    predictive = _predictive([
        ("1-0", 0.22),
        ("2-1", 0.20),
        ("3-2", 0.18),
        ("2-0", 0.16),
        ("3-0", 0.12),
    ])
    out = select_direction_consistent_top3(
        predictive,
        execution_path={
            "winner": "HOME",
            "ah": {"formal": True, "hard_gate": True, "home_handicap": -1.0, "backing": "HOME"},
        },
    )
    scores = [row["score"] for row in out["top3"]]
    assert "1-0" not in scores
    assert "2-1" not in scores
    assert "3-2" not in scores
    assert scores == ["2-0", "3-0"]
    raw = {row["score"]: row for row in out["raw_top10"]}
    assert raw["1-0"]["ah_payoff"] == 0.0
    assert raw["1-0"]["ah_ok"] is False


def test_favorite_minus_one_seventy_five_rejects_two_one_but_allows_positive_half_win():
    predictive = _predictive([
        ("2-1", 0.24),
        ("2-0", 0.20),
        ("3-1", 0.18),
        ("3-0", 0.15),
    ])
    out = select_direction_consistent_top3(
        predictive,
        execution_path={
            "winner": "HOME",
            "ah": {"formal": True, "hard_gate": True, "home_handicap": -1.75, "backing": "HOME"},
        },
    )
    scores = [row["score"] for row in out["top3"]]
    assert "2-1" not in scores
    assert "2-0" in scores
    assert "3-1" in scores
    raw = {row["score"]: row for row in out["raw_top10"]}
    assert raw["2-1"]["ah_payoff"] < 0.0
    assert raw["2-0"]["ah_payoff"] > 0.0
    assert raw["3-1"]["ah_payoff"] > 0.0
