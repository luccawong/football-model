from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import yaml


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold().strip()
    return re.sub(r"[^\w\u3400-\u9fff]+", "", value)


def _fallback_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(normalize(value).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


@dataclass(frozen=True)
class CanonicalName:
    canonical_id: str
    canonical_name: str
    registered: bool


class AliasRegistry:
    def __init__(self, config_dir: Path | None = None):
        config_dir = config_dir or Path(__file__).with_name("config")
        self.team_aliases, self.team_names = self._load(config_dir / "team_aliases.yaml", "teams")
        self.competition_aliases, self.competition_names = self._load(
            config_dir / "competition_aliases.yaml", "competitions"
        )

    @staticmethod
    def _load(path: Path, key: str) -> tuple[dict[str, str], dict[str, str]]:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        aliases: dict[str, str] = {}
        names: dict[str, str] = {}
        for canonical_id, values in (payload.get(key) or {}).items():
            if not isinstance(values, list) or not values:
                raise ValueError(f"{path}: {canonical_id} must have a non-empty alias list")
            names[canonical_id] = str(values[0])
            for value in values:
                token = normalize(str(value))
                previous = aliases.get(token)
                if previous and previous != canonical_id:
                    raise ValueError(f"alias collision in {path}: {value}")
                aliases[token] = canonical_id
        return aliases, names

    def team(self, value: str) -> CanonicalName:
        canonical_id = self.team_aliases.get(normalize(value))
        if canonical_id:
            return CanonicalName(canonical_id, self.team_names[canonical_id], True)
        return CanonicalName(_fallback_id("team", value), value.strip(), False)

    def competition(self, value: str) -> CanonicalName:
        canonical_id = self.competition_aliases.get(normalize(value))
        if canonical_id:
            return CanonicalName(canonical_id, self.competition_names[canonical_id], True)
        return CanonicalName(_fallback_id("competition", value), value.strip(), False)

