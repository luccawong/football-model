from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from difflib import SequenceMatcher

from . import AMBIGUOUS_MATCH, MATCHED_EXCLUDED, MATCHED_NOT_EXCLUDED, MATCH_FAILED
from .aliases import AliasRegistry, normalize


@dataclass(frozen=True)
class MatchResult:
    status: str
    external_draw_exclusion_label: int | None
    research_match_id: str | None
    titan_match_id: str | None
    snapshot_id: str | None
    matched_by: str | None
    confidence: float | None
    candidate_count: int
    candidates: tuple[str, ...] = ()
    review_required: bool = False

    def to_dict(self) -> dict:
        result = asdict(self)
        result["candidates"] = list(self.candidates)
        return result


class SourcePoolMatcher:
    """Conservative matcher: fuzzy similarity can suggest, never label."""

    def __init__(self, rows: list[dict], aliases: AliasRegistry | None = None):
        self.rows = rows
        self.aliases = aliases or AliasRegistry()

    @staticmethod
    def _result(row: dict, matched_by: str, confidence: float) -> MatchResult:
        label = row["external_draw_exclusion_label"]
        status = MATCHED_EXCLUDED if label == 1 else MATCHED_NOT_EXCLUDED
        return MatchResult(
            status, label, row["research_match_id"], row.get("titan_match_id"), row.get("snapshot_id"),
            matched_by, confidence, 1
        )

    def match(
        self,
        *,
        date: str,
        home_team: str,
        away_team: str,
        kickoff_time: str | None = None,
        competition: str | None = None,
    ) -> MatchResult:
        home_id = self.aliases.team(home_team).canonical_id
        away_id = self.aliases.team(away_team).canonical_id
        competition_id = self.aliases.competition(competition).canonical_id if competition else None
        same_day = [row for row in self.rows if row["kickoff_time"][:10] == date]
        team_matches = [
            row for row in same_day
            if row["home_team"]["canonical_id"] == home_id and row["away_team"]["canonical_id"] == away_id
            and (competition_id is None or row["competition"]["canonical_id"] == competition_id)
        ]
        unique_outcomes = {
            (row["research_match_id"], row["external_draw_exclusion_label"]) for row in team_matches
        }
        if len(unique_outcomes) == 1 and team_matches:
            team_matches = [team_matches[0]]
        if len(team_matches) == 1:
            row = team_matches[0]
            if not kickoff_time:
                return self._result(row, "L1_DATE_CANONICAL_TEAMS", 0.98)
            target = datetime.fromisoformat(kickoff_time)
            observed = datetime.fromisoformat(row["kickoff_time"])
            minutes = abs((target - observed).total_seconds()) / 60
            if minutes <= 30:
                return self._result(row, "L2_ALIASES_TIME_WINDOW_30M", 0.95)
            if any(abs(minutes - offset) <= 5 for offset in (60, 480)):
                return self._result(row, "L3_TIMEZONE_OFFSET", 0.85)
        if len(team_matches) > 1:
            return MatchResult(
                AMBIGUOUS_MATCH, None, None, None, None, None, None, len(team_matches),
                tuple(row["research_match_id"] for row in team_matches), True,
            )

        # Suggestions are intentionally non-authoritative and never generate 0/1.
        suggestions: list[tuple[float, str]] = []
        query = normalize(home_team) + "|" + normalize(away_team)
        for row in same_day:
            candidate = normalize(row["home_team"]["raw_name"]) + "|" + normalize(row["away_team"]["raw_name"])
            ratio = SequenceMatcher(None, query, candidate).ratio()
            if ratio >= 0.88:
                suggestions.append((ratio, row["research_match_id"]))
        suggestions.sort(reverse=True)
        return MatchResult(
            MATCH_FAILED, None, None, None, None, "FUZZY_SUGGESTION_ONLY" if suggestions else None,
            suggestions[0][0] if suggestions else None, len(suggestions),
            tuple(item[1] for item in suggestions[:5]), bool(suggestions),
        )
