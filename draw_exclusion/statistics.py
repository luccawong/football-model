"""Separate prospective exclusion accuracy; NOT_EXCLUDED is not a draw prediction."""
from __future__ import annotations

from datetime import datetime
import sqlite3


def market_statistics(connection: sqlite3.Connection) -> dict:
    rows = [dict(row) for row in connection.execute("SELECT * FROM research_evaluation")]
    frozen, outcomes, outcome_conflicts = {}, {}, set()
    for row in rows:
        identity = row["research_match_id"]
        if row["final_is_draw"] in (0, 1):
            outcomes.setdefault(identity, set()).add(row["final_is_draw"])
            if len(outcomes[identity]) > 1:
                outcome_conflicts.add(identity)
        stamp = row["external_label_snapshot_time"]
        if not stamp or row["external_draw_exclusion_label"] not in (0, 1):
            continue
        if datetime.fromisoformat(stamp) >= datetime.fromisoformat(row["kickoff_time"]):
            continue
        key = (identity, row["source_market"])
        if key not in frozen or datetime.fromisoformat(stamp) < datetime.fromisoformat(frozen[key]["external_label_snapshot_time"]):
            frozen[key] = row

    def report(selected: list[dict]) -> dict:
        scored = [r for r in selected if r["research_match_id"] in outcomes
                  and r["research_match_id"] not in outcome_conflicts]
        failed = sum(next(iter(outcomes[r["research_match_id"]])) == 1 for r in scored)
        return {"samples": len(selected), "evaluated": len(scored),
                "pending_or_conflicting_outcome": len(selected) - len(scored),
                "hits": len(scored) - failed, "failures": failed,
                "hit_rate": (len(scored) - failed) / len(scored) if scored else None,
                "failure_types": {"ACTUAL_DRAW": failed}}

    result = {m: report([r for (_, market), r in frozen.items()
                        if market == m and r["external_draw_exclusion_label"] == 1])
              for m in ("JC", "BD")}
    for leader, other in (("JC", "BD"), ("BD", "JC")):
        selected = [r for (identity, market), r in frozen.items() if market == leader
                    and r["external_draw_exclusion_label"] == 1
                    and (identity, other) in frozen
                    and frozen[(identity, other)]["external_draw_exclusion_label"] == 0]
        result[f"{leader}_EXCLUDE_{other}_NOT_EXCLUDED"] = report(selected)
    result["freeze_policy"] = "FIRST_OBSERVED_PRE_KICKOFF_PER_MARKET"
    result["leading_definition"] = "EXCLUDE_VS_NOT_EXCLUDED; not temporal precedence"
    result["outcome_conflicts"] = sorted(outcome_conflicts)
    return result


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path(__file__).resolve().parent / "database/draw_exclusion.sqlite")
    args = parser.parse_args()
    connection = sqlite3.connect(args.database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        print(json.dumps(market_statistics(connection), ensure_ascii=False, indent=2))
    finally:
        connection.close()
