from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from src.index.match_index_builder import normalize
from src.normalization.formats import line_value


BEIJING = ZoneInfo("Asia/Shanghai")


class DrawSiteParseError(ValueError):
    """Raised when the static report no longer matches the audited contract."""


@dataclass(frozen=True)
class SiteMatch:
    research_match_id: str
    source_market: str
    site_row_index: int
    site_data_key: str
    competition: str
    match_number: str
    home_team: str
    away_team: str
    kickoff_time: str
    is_single_game: bool
    visible_home_1x2: float | None
    visible_draw_1x2: float | None
    visible_away_1x2: float | None
    visible_asian_handicap: float | None
    visible_asian_handicap_raw: str | None
    visible_home_water: float | None
    visible_away_water: float | None
    website_draw_exclusion_label: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ParsedPage:
    page_reported_update_time: str | None
    matches: tuple[SiteMatch, ...]
    label_indices: dict[str, tuple[int, ...]]


def _float(text: str | None) -> float | None:
    if text is None:
        return None
    try:
        return float(text.strip())
    except (TypeError, ValueError):
        return None


def _decode_label_indices(html: str) -> dict[str, tuple[int, ...]]:
    match = re.search(
        r"var\s+_mk\s*=\s*\[([\d,\s]+)\]\.map\(function\s*\(c\)\s*\{\s*"
        r"return\s+String\.fromCharCode\(c\s*-\s*(\d+)\);?\s*\}\)\.join\(['\"]['\"]\)",
        html,
    )
    if not match:
        raise DrawSiteParseError("encoded label payload _mk was not found")
    numbers = [int(value) for value in match.group(1).split(",") if value.strip()]
    shift = int(match.group(2))
    try:
        decoded = "".join(chr(value - shift) for value in numbers)
        payload = json.loads(decoded)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise DrawSiteParseError("encoded label payload could not be decoded") from exc

    # The audited draw-exclusion contract only owns the first two groups:
    # JC and BD. The site may append unrelated groups (for example a
    # recommendation page). Those groups must not block or enter the draw
    # exclusion pipeline. We still fail closed if either core group changes
    # shape, because that would affect the labels we actually consume.
    if not isinstance(payload, list) or len(payload) < 2:
        raise DrawSiteParseError("encoded label payload has an unexpected shape")
    core_groups = payload[:2]
    if (
        any(not isinstance(group, list) for group in core_groups)
        or any(not isinstance(index, int) for group in core_groups for index in group)
    ):
        raise DrawSiteParseError("encoded label payload has an unexpected shape")
    return {"JC": tuple(core_groups[0]), "BD": tuple(core_groups[1])}


def _teams(cell) -> tuple[str, str]:
    clone = BeautifulSoup(str(cell), "html.parser")
    for badge in clone.select(".rq-badge, .sg-badge, .jc-badge, .bd-badge"):
        badge.decompose()
    text = clone.get_text(" ", strip=True)
    parts = re.split(r"\s+vs\s+", text, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2 or not all(part.strip() for part in parts):
        raise DrawSiteParseError(f"could not split fixture teams: {text!r}")
    return parts[0].strip(), parts[1].strip()


def _kickoff(text: str) -> str:
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d %H:%M").replace(tzinfo=BEIJING).isoformat(timespec="seconds")
    except ValueError as exc:
        raise DrawSiteParseError(f"invalid kickoff time: {text!r}") from exc


def research_match_id(competition: str, home: str, away: str, kickoff_time: str) -> str:
    canonical = "\x1f".join(
        [normalize(competition), normalize(home), normalize(away), datetime.fromisoformat(kickoff_time).isoformat()]
    )
    return "drm_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_table(soup: BeautifulSoup, table_id: str, source_market: str, labels: set[int]) -> list[SiteMatch]:
    table = soup.select_one(f"#{table_id}")
    if table is None:
        raise DrawSiteParseError(f"required current table #{table_id} was not found")
    result: list[SiteMatch] = []
    seen_indices: set[int] = set()
    for row in table.select("tbody tr"):
        try:
            index = int(row.get("data-idx"))
        except (TypeError, ValueError) as exc:
            raise DrawSiteParseError(f"table #{table_id} has a row without a numeric data-idx") from exc
        if index in seen_indices:
            raise DrawSiteParseError(f"table #{table_id} has duplicate data-idx {index}")
        seen_indices.add(index)
        team_cell = row.select_one("td.c-team")
        if team_cell is None:
            raise DrawSiteParseError(f"table #{table_id} row {index} has no fixture cell")
        home, away = _teams(team_cell)
        competition_cell = row.select_one("td.c-league")
        number_cell = row.select_one("td.c-no")
        time_cell = row.select_one("td.c-time")
        if not competition_cell or not number_cell or not time_cell:
            raise DrawSiteParseError(f"table #{table_id} row {index} is missing identity fields")
        competition = competition_cell.get_text(" ", strip=True)
        kickoff = _kickoff(time_cell.get_text(" ", strip=True))
        odds = row.select_one("td.c-jc-odds")
        visible_1x2 = [None, None, None]
        if odds is not None:
            visible_1x2 = [
                _float((odds.select_one(selector) or {}).get_text(strip=True) if odds.select_one(selector) else None)
                for selector in (".oh", ".od", ".oa")
            ]
        ah = row.select_one("td.c-ah")
        line_element = ah.select_one(".ah-line") if ah else None
        line_raw = line_element.get_text(" ", strip=True) if line_element else None
        waters = ah.select(".ah-w") if ah else []
        result.append(
            SiteMatch(
                research_match_id=research_match_id(competition, home, away, kickoff),
                source_market=source_market,
                site_row_index=index,
                site_data_key=row.get("data-key") or "",
                competition=competition,
                match_number=number_cell.get_text(" ", strip=True),
                home_team=home,
                away_team=away,
                kickoff_time=kickoff,
                is_single_game=row.get("data-single") == "1",
                visible_home_1x2=visible_1x2[0],
                visible_draw_1x2=visible_1x2[1],
                visible_away_1x2=visible_1x2[2],
                visible_asian_handicap=line_value(line_raw, "ah") if line_raw else None,
                visible_asian_handicap_raw=line_raw,
                visible_home_water=_float(waters[0].get_text(strip=True)) if len(waters) >= 1 else None,
                visible_away_water=_float(waters[-1].get_text(strip=True)) if len(waters) >= 2 else None,
                website_draw_exclusion_label=1 if index in labels else 0,
            )
        )
    unknown_labels = labels - seen_indices
    if unknown_labels:
        raise DrawSiteParseError(f"label indices do not exist in #{table_id}: {sorted(unknown_labels)}")
    return result


def parse_page(html: str) -> ParsedPage:
    labels = _decode_label_indices(html)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    update = re.search(r"更新时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", text)
    reported = None
    if update:
        reported = datetime.strptime(update.group(1), "%Y-%m-%d %H:%M").replace(tzinfo=BEIJING).isoformat(timespec="seconds")
    matches = _parse_table(soup, "tbl", "JC", set(labels["JC"]))
    matches.extend(_parse_table(soup, "bdtbl", "BD", set(labels["BD"])))
    return ParsedPage(page_reported_update_time=reported, matches=tuple(matches), label_indices=labels)
