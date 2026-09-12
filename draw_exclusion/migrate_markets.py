"""Rebuild market indexes and add SQLite market views; preserve frozen evidence."""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .database.repository import connect
from .indexer import rebuild_index


def migrate(root: Path) -> dict:
    database = root / "database" / "draw_exclusion.sqlite"
    backup = None
    foreign_keys = None
    if database.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        backup = database.with_name(f"draw_exclusion.pre_markets_{stamp}.sqlite")
        with sqlite3.connect(database) as source, sqlite3.connect(backup) as target:
            source.backup(target)
        connection = connect(database)
        try:
            foreign_keys = len(connection.execute("PRAGMA foreign_key_check").fetchall())
            if foreign_keys:
                raise ValueError(f"Database has {foreign_keys} foreign key violations")
        finally:
            connection.close()
    index = rebuild_index(root)
    return {"schema_version": index["schema_version"],
            "market_rows": {m: len(v["by_research_match_id"]) for m, v in index["by_market"].items()},
            "latest_date": index["latest_date"], "foreign_key_violations": foreign_keys,
            "database_backup": str(backup) if backup else None,
            "frozen_manifests_rewritten": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(json.dumps(migrate(args.root), ensure_ascii=False, indent=2))
