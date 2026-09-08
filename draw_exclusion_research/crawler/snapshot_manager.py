from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .draw_site_collector import HttpSnapshot


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

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def _atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def store_snapshot(project_root: Path, snapshot: HttpSnapshot, page_reported_update_time: str | None) -> StoredSnapshot:
    captured_utc = snapshot.captured_at_utc.astimezone(timezone.utc)
    captured_beijing = captured_utc.astimezone(BEIJING)
    day_directory = project_root / "raw" / "draw_site" / captured_beijing.date().isoformat()
    day_directory.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(snapshot.html_bytes).hexdigest()
    base = captured_beijing.strftime("%Y%m%d_%H%M%S")
    html_path = day_directory / f"{base}.html"
    suffix = 1
    while html_path.exists():
        html_path = day_directory / f"{base}_{suffix:02d}.html"
        suffix += 1
    html_path.write_bytes(snapshot.html_bytes)

    metadata_path = day_directory / "metadata.json"
    metadata = {"schema_version": "1.0", "captures": []}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    previous = metadata["captures"][-1] if metadata["captures"] else None
    hashes = []
    for capture in metadata["captures"]:
        if capture["sha256"] not in hashes:
            hashes.append(capture["sha256"])
    if digest not in hashes:
        hashes.append(digest)
    version = hashes.index(digest) + 1
    captured_iso = captured_utc.isoformat(timespec="seconds")
    snapshot_id = "snap_" + hashlib.sha256(f"{captured_iso}|{digest}|{html_path.name}".encode()).hexdigest()
    relative_html = html_path.relative_to(project_root).as_posix()
    stored = StoredSnapshot(
        snapshot_id=snapshot_id,
        snapshot_time_utc=captured_iso,
        snapshot_time_beijing=captured_beijing.isoformat(timespec="seconds"),
        source_url=snapshot.source_url,
        http_date=snapshot.http_date,
        last_modified=snapshot.last_modified,
        page_reported_update_time=page_reported_update_time,
        sha256=digest,
        html_size=len(snapshot.html_bytes),
        html_path=relative_html,
        content_version=version,
        same_hash_as_previous=None if previous is None else previous["sha256"] == digest,
    )
    metadata["captures"].append(stored.to_dict())
    _atomic_json(metadata_path, metadata)
    return stored
