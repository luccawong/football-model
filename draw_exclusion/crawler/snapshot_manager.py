from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .fetch_draw_site import HttpSnapshot


BEIJING = ZoneInfo("Asia/Shanghai")


@dataclass(frozen=True)
class StoredSnapshot:
    snapshot_id: str
    snapshot_time_utc: str
    snapshot_time_beijing: str
    source_url: str
    http_date: str | None
    last_modified: str | None
    page_reported_update_time: str | None
    sha256: str
    html_size: int
    html_path: str
    content_version: int
    same_hash_as_previous: bool | None
    manual_screenshot_present: bool

    def to_dict(self) -> dict:
        return asdict(self)


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def store_snapshot(root: Path, snapshot: HttpSnapshot, page_update: str | None) -> StoredSnapshot:
    captured_utc = snapshot.captured_at_utc.astimezone(timezone.utc)
    captured_bj = captured_utc.astimezone(BEIJING)
    day = captured_bj.date().isoformat()
    day_directory = root / "raw" / day
    day_directory.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(snapshot.html_bytes).hexdigest()

    metadata_path = day_directory / "metadata.json"
    metadata = {"schema_version": "2.0", "captures": []}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    prior = metadata["captures"][-1] if metadata["captures"] else None
    unique_hashes = list(dict.fromkeys(item["sha256"] for item in metadata["captures"]))
    version_manifests = sorted((root / "daily" / "versions" / day).glob("*.json"))
    tracked_captures = []
    for path in version_manifests:
        try:
            tracked_captures.append(json.loads(path.read_text(encoding="utf-8"))["snapshot"])
        except (KeyError, json.JSONDecodeError):
            continue
    if prior is None and tracked_captures:
        prior = max(tracked_captures, key=lambda item: item["snapshot_time_beijing"])
    for item in tracked_captures:
        if item["sha256"] not in unique_hashes:
            unique_hashes.append(item["sha256"])
    if digest not in unique_hashes:
        unique_hashes.append(digest)
    version = unique_hashes.index(digest) + 1
    basename = f"snapshot_v{version}_{captured_bj.strftime('%Y%m%d_%H%M%S')}"
    html_path = day_directory / f"{basename}.html"
    suffix = 1
    while html_path.exists():
        html_path = day_directory / f"{basename}_{suffix:02d}.html"
        suffix += 1
    html_path.write_bytes(snapshot.html_bytes)

    screenshot_dir = root / "screenshots" / day
    screenshot_present = screenshot_dir.is_dir() and any(path.is_file() for path in screenshot_dir.iterdir())
    captured_iso = captured_utc.isoformat(timespec="seconds")
    snapshot_id = "snap_" + hashlib.sha256(
        f"{captured_iso}|{digest}|{html_path.name}".encode("utf-8")
    ).hexdigest()
    stored = StoredSnapshot(
        snapshot_id=snapshot_id,
        snapshot_time_utc=captured_iso,
        snapshot_time_beijing=captured_bj.isoformat(timespec="seconds"),
        source_url=snapshot.source_url,
        http_date=snapshot.http_date,
        last_modified=snapshot.last_modified,
        page_reported_update_time=page_update,
        sha256=digest,
        html_size=len(snapshot.html_bytes),
        html_path=html_path.relative_to(root).as_posix(),
        content_version=version,
        same_hash_as_previous=None if prior is None else prior["sha256"] == digest,
        manual_screenshot_present=screenshot_present,
    )
    metadata["captures"].append(stored.to_dict())
    atomic_json(metadata_path, metadata)
    return stored
