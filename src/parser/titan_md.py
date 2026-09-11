from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


TABLE_HEADING = re.compile(r"^### .*?\(`([^`]+)`\).*?(\d+) rows$")


def read_markdown_tables(path: str | Path) -> dict[str, list[dict[str, Any]]]:
    return read_markdown_tables_text(Path(path).read_text(encoding="utf-8"))


def read_markdown_tables_text(text: str) -> dict[str, list[dict[str, Any]]]:
    tables: dict[str, list[dict[str, Any]]] = defaultdict(list)
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = TABLE_HEADING.match(lines[i].strip())
        if not m:
            i += 1
            continue
        table_name = m.group(1)
        i += 1
        while i < len(lines) and lines[i].strip() not in {"```jsonl", "```json"}:
            i += 1
        if i >= len(lines):
            break
        i += 1
        while i < len(lines) and lines[i].strip() != "```":
            raw = lines[i].strip()
            if raw:
                obj = json.loads(raw)
                if isinstance(obj, dict):
                    tables[table_name].append(obj)
            i += 1
        i += 1
    return dict(tables)
