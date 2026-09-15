"""Research-only Titan team goal baselines for the big five leagues."""

from .engine import (
    DEFAULT_VARIANTS,
    FIVE_LEAGUES,
    BaselineError,
    classify_team_goal_market_deviation,
    compare_market_lambda,
    load_completed_matches,
    matchup_lambda,
)

__all__ = [
    "DEFAULT_VARIANTS",
    "FIVE_LEAGUES",
    "BaselineError",
    "compare_market_lambda",
    "load_completed_matches",
    "matchup_lambda",
]
