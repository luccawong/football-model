from __future__ import annotations

import hashlib
import json
from pathlib import Path

from draw_exclusion_research.crawler.draw_site_parser import ParsedPage

from draw_exclusion.aliases import AliasRegistry
from draw_exclusion.crawler.snapshot_manager import StoredSnapshot, atomic_json


def _research_id(competition_id: str, home_id: str, away_id: str, kickoff: str) -> str:
    identity = "\x1f".join((competition_id, home_id, away_id, kickoff))
    return "drm_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _manual_labels(root: Path) -> dict[str, dict]:
    payload = json.loads((root / "manual_labels.json").read_text(encoding="utf-8"))
    return {item["research_match_id"]: item for item in payload.get("labels", []) if item.get("active", True)}


def _forensic_claims(root: Path) -> dict[str, list[dict]]:
    payload = json.loads((root / "forensic_evidence.json").read_text(encoding="utf-8"))
    claims: dict[str, list[dict]] = {}
    for item in payload.get("items", []):
        if item.get("verified") and item.get("claimed_label") in (0, 1):
            claims.setdefault(item["research_match_id"], []).append(item)
    return claims


def build_manifest(
    root: Path,
    page: ParsedPage,
    snapshot: StoredSnapshot,
    resolutions: dict[tuple[str, str], dict],
    snapshot_diff: dict,
    source_status: str = "OK",
) -> dict:
    aliases = AliasRegistry(root / "config")
    manual = _manual_labels(root)
    forensic = _forensic_claims(root)
    rows = []
    forensic_conflicts = []
    for match in page.matches:
        competition = aliases.competition(match.competition)
        home = aliases.team(match.home_team)
        away = aliases.team(match.away_team)
        research_id = _research_id(
            competition.canonical_id, home.canonical_id, away.canonical_id, match.kickoff_time
        )
        resolution = resolutions.get((match.research_match_id, match.source_market), {})
        website_label = match.website_draw_exclusion_label
        manual_item = manual.get(research_id)
        # A verified automatic snapshot has higher priority than a manual assertion.
        effective_label = website_label
        origin = "VERIFIED_AUTOMATIC_SNAPSHOT"
        provenance = [{
            "origin": origin,
            "snapshot_id": snapshot.snapshot_id,
            "source_url": snapshot.source_url,
            "sha256": snapshot.sha256,
        }]
        if manual_item:
            provenance.append({
                "origin": "USER_MANUAL",
                "label": manual_item["label"],
                "entered_at": manual_item.get("entered_at"),
                "note": manual_item.get("note"),
                "superseded_by": origin,
            })
        for claim in forensic.get(research_id, []):
            provenance.append({
                "origin": "VERIFIED_MANUAL_SCREENSHOT",
                "label": claim["claimed_label"],
                "path": claim.get("path"),
                "verified_by": claim.get("verified_by"),
                "superseded_by": origin,
            })
            if claim["claimed_label"] != website_label:
                forensic_conflicts.append({
                    "status": "FORENSIC_CONFLICT",
                    "research_match_id": research_id,
                    "automatic_label": website_label,
                    "screenshot_label": claim["claimed_label"],
                    "screenshot_path": claim.get("path"),
                })
        rows.append({
            "research_match_id": research_id,
            "source_research_match_id": match.research_match_id,
            "titan_match_id": resolution.get("match_id"),
            "source_market": match.source_market,
            "competition": {
                "raw_name": match.competition,
                "canonical_id": competition.canonical_id,
                "canonical_name": competition.canonical_name,
                "alias_registered": competition.registered,
            },
            "match_number": match.match_number,
            "home_team": {
                "raw_name": match.home_team,
                "canonical_id": home.canonical_id,
                "canonical_name": home.canonical_name,
                "alias_registered": home.registered,
            },
            "away_team": {
                "raw_name": match.away_team,
                "canonical_id": away.canonical_id,
                "canonical_name": away.canonical_name,
                "alias_registered": away.registered,
            },
            "kickoff_time": match.kickoff_time,
            "external_draw_exclusion_label": effective_label,
            "external_label_status": "EXCLUDED" if effective_label == 1 else "NOT_EXCLUDED",
            "label_origin": origin,
            "source_data_key": match.site_data_key,
            "source_row_index": match.site_row_index,
            "snapshot_id": snapshot.snapshot_id,
            "titan_resolution": {
                "status": resolution.get("status", "unavailable"),
                "matched_by": resolution.get("matched_by"),
                "confidence": 1.0 if resolution.get("status") == "resolved" else None,
            },
            "visible_odds": {
                "home_1x2": match.visible_home_1x2,
                "draw_1x2": match.visible_draw_1x2,
                "away_1x2": match.visible_away_1x2,
                "asian_handicap": match.visible_asian_handicap,
                "asian_handicap_raw": match.visible_asian_handicap_raw,
                "home_water": match.visible_home_water,
                "away_water": match.visible_away_water,
            },
            "provenance": provenance,
        })
    source_date = (page.page_reported_update_time or snapshot.snapshot_time_beijing)[:10]
    return {
        "schema_version": "2.0",
        "date": source_date,
        "source": "external_draw_site",
        "source_status": source_status,
        "snapshot": snapshot.to_dict(),
        "snapshot_diff": snapshot_diff,
        "label_contract": {"1": "EXCLUDED", "0": "NOT_EXCLUDED", "null": "UNKNOWN"},
        "forensic_conflicts": forensic_conflicts,
        "matches": rows,
    }


def write_manifest(root: Path, manifest: dict, promote: bool = True) -> tuple[Path, Path]:
    day = manifest["date"]
    version = manifest["snapshot"]["content_version"]
    digest = manifest["snapshot"]["sha256"][:12]
    version_path = root / "daily" / "versions" / day / f"v{version}_{digest}.json"
    if not version_path.exists():
        atomic_json(version_path, manifest)
    daily_path = root / "daily" / f"{day}.json"
    if promote:
        atomic_json(daily_path, manifest)
    return daily_path, version_path
