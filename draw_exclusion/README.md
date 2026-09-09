# External Draw Exclusion Label Layer

This module freezes and exposes an external **teacher label**. It does not
replace the football model and must never be used to remove the draw outcome
without the independent Draw Exclusion analysis.

## Label contract

| Value | Meaning | When it is legal |
|---|---|---|
| `1` | `EXCLUDED` | Match is present in a verified source pool and marked 排平 |
| `0` | `NOT_EXCLUDED` | Match is present in a verified source pool and not marked 排平 |
| `null` | `UNKNOWN` | Snapshot missing, match outside pool, ambiguous, or match failed |

Absence is never converted to zero. Query statuses are
`MATCHED_EXCLUDED`, `MATCHED_NOT_EXCLUDED`, `NOT_IN_SOURCE_POOL`,
`SOURCE_SNAPSHOT_MISSING`, `AMBIGUOUS_MATCH`, and `MATCH_FAILED`.

## Daily collection

```bash
python scripts/run_draw_exclusion_daily.py
```

The source URL lives in `config/settings.json`; replace only `source_url` when
the site moves. Never put a password, cookie, or temporary access token in that
file. Each run freezes a unique local HTML file, parses every JC and BD row,
writes an immutable version manifest, promotes a date manifest only when the
page-reported Beijing date is current, rebuilds `index.json`/`latest.json`,
updates SQLite, and emits QC.

Raw HTML and SQLite are intentionally ignored by Git because source HTML can
contain access-gate code or credentials. GitHub Actions stores them as a
private 30-day run artifact; versioned manifests, hashes, provenance, diffs,
indexes, and QC reports are committed to the repository.

## Query

Prefer Titan ID:

```bash
python draw_exclusion/query_label.py --match-id 3049507
```

Fallback to canonical fixture matching:

```bash
python draw_exclusion/query_label.py --date 2026-09-09 --league 瑞典超 --home 哥德堡 --away 马尔默 --kickoff 20:00
```

For ChatGPT/Codex, fetch `draw_exclusion/index.json`, look first in
`by_titan_match_id`, and only then load the relevant daily manifest. If no
record is found, return `UNKNOWN`; never infer `NOT_EXCLUDED`.

## Evidence and overrides

HTML is primary. Screenshots are forensic evidence only and belong in
`screenshots/YYYY-MM-DD/`. Manual assertions belong in `manual_labels.json`
with `origin=USER_MANUAL`, timestamp, author, and note. Provenance priority is:

1. verified automatic snapshot;
2. verified manual screenshot;
3. explicit user manual label;
4. unknown.

A screenshot conflict is reported as `FORENSIC_CONFLICT`; neither side is
deleted. Fuzzy team similarity can create a review suggestion but cannot
produce a binary label.

