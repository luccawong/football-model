from __future__ import annotations

import json
from pathlib import Path

from src.index.match_resolver import MatchResolver, load_index

from draw_exclusion_research.crawler.draw_site_parser import SiteMatch
from draw_exclusion_research.database.repository import insert_external_event


class TitanAdapter:
    """Exact/alias-only bridge into existing validated Titan packets."""

    def __init__(self, football_model_root: Path):
        self.root = football_model_root
        registry_path = self.root / "config" / "team_aliases.json"
        self.available = registry_path.is_file() and (self.root / "validation_packets").is_dir()
        self.registry = json.loads(registry_path.read_text(encoding="utf-8")) if self.available else {"leagues": {}}
        self.index = load_index(self.root) if self.available else []
        self.resolver = MatchResolver(self.index, self.registry)
        self._packet_cache: dict[str, dict] = {}

    def resolve(self, match: SiteMatch) -> dict:
        if not self.available or not self.index:
            return {
                "status": "unavailable",
                "match_id": None,
                "confidence": None,
                "matched_by": None,
                "candidate_count": 0,
                "candidates": [],
            }
        kickoff_date = match.kickoff_time[:10]
        return self.resolver.resolve_match(
            f"{match.home_team} vs {match.away_team}",
            date=kickoff_date,
        )

    def _packet(self, resolution: dict) -> dict | None:
        if resolution.get("status") != "resolved":
            return None
        batch = (resolution.get("resolved_from") or {}).get("batch_file")
        titan_id = resolution.get("match_id")
        if not batch or not titan_id:
            return None
        if batch not in self._packet_cache:
            path = self.root / batch
            self._packet_cache[batch] = json.loads(path.read_text(encoding="utf-8"))
        return self._packet_cache[batch].get("matches", {}).get(str(titan_id))

    def ingest_timeline(self, connection, match: SiteMatch, resolution: dict) -> dict[str, int]:
        packet = self._packet(resolution)
        counts = {"1x2": 0, "ah": 0, "ou": 0}
        if packet is None:
            return counts
        titan_id = str(resolution["match_id"])
        for market in counts:
            histories = packet.get("timeline", {}).get(market, {})
            for events in histories.values():
                for event in events:
                    if insert_external_event(
                        connection,
                        match.research_match_id,
                        titan_id,
                        market,
                        event,
                        "football-model/Titan",
                    ):
                        counts[market] += 1
        return counts
