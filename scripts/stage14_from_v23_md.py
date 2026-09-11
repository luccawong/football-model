from __future__ import annotations

import argparse
import json

from gpt.quant_core import build_quant_packet
from gpt.stage14_auto import automatic_top3
from src.parser.titan_md import read_markdown_tables


CORE = ("Pinnacle", "Bet365", "Macau")


def parse_line(value):
    text = str(value).strip()
    if "/" in text:
        parts = [float(x) for x in text.split("/")]
        return sum(parts) / len(parts)
    return float(text)


def build_payload(tables, match_id):
    companies = {}
    euro = [r for r in tables.get("Europe_1x2", []) if str(r.get("match_id")) == str(match_id)]
    ou = [r for r in tables.get("OverUnder_Current", []) if str(r.get("match_id")) == str(match_id)]

    for row in euro:
        name = row.get("company")
        if not name:
            continue
        prices = [row.get("current_home"), row.get("current_draw"), row.get("current_away")]
        if all(v is not None for v in prices):
            companies.setdefault(name, {})["one_x_two"] = [float(v) for v in prices]

    for row in ou:
        name = row.get("company")
        if not name or row.get("current_line") is None:
            continue
        if row.get("current_left") is None or row.get("current_right") is None:
            continue
        companies.setdefault(name, {})["ou"] = {
            "line": parse_line(row["current_line"]),
            "over": 1.0 + float(row["current_left"]),
            "under": 1.0 + float(row["current_right"]),
            "role": "dynamic" if name in CORE else "reference",
        }

    usable = {name: data for name, data in companies.items() if "one_x_two" in data and "ou" in data}
    return {"match_id": str(match_id), "companies": usable}


def build_stage14(path, match_id):
    tables = read_markdown_tables(path)
    quant = build_quant_packet(build_payload(tables, match_id))
    available = quant.get("reconstruction", {})
    company = next((name for name in CORE if name in available), None)
    if company is None:
        return {"match_id": str(match_id), "status": "MISSING", "reason": "NO_CORE_RECONSTRUCTION"}
    score = automatic_top3(quant, company)
    return {
        "match_id": str(match_id),
        "research_only": True,
        "quant_engine_version": quant.get("engine_version"),
        "company": company,
        "stage14": score,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown")
    parser.add_argument("match_id")
    args = parser.parse_args()
    print(json.dumps(build_stage14(args.markdown, args.match_id), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
