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
python draw_exclusion/query_label.py --match-id 3049507 --market JC
python draw_exclusion/query_label.py --match-id 3049507 --market BD
```

Fallback to canonical fixture matching:

```bash
python draw_exclusion/query_label.py --market JC --date 2026-09-09 --league 瑞典超 --home 哥德堡 --away 马尔默 --kickoff 20:00
```

For ChatGPT/Codex, fetch `draw_exclusion/index.json`, look first in
`by_market.JC.by_titan_match_id` and `by_market.BD.by_titan_match_id` independently,
and only then load the relevant daily manifest. If no
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

## Market isolation (schema 3.0)

The stable fixture `research_match_id` and Titan crosswalk are preserved.
The label identity is `market_key = research_match_id + "|" + source_market`.
SQLite already uses market-inclusive compound keys; `jc_layer` and `bd_layer`
views now expose the six explicitly prefixed evidence fields for each market.
Existing generic label columns are retained only inside market-scoped rows for
crawler compatibility; there is no combined fixture label.

New manifests contain both `JC_layer` and `BD_layer` on fixture rows.
Each layer contains its own label, status, snapshot ID/time, source and provenance.
Missing evidence stays null. A same-market conflict remains ambiguous with its
candidates retained; JC/BD disagreement is not an ambiguity or QC failure.

`index.json` keeps its filename, date indexes and Titan identifiers. Its v3
`by_titan_match_id[id]` / `by_research_match_id[id]` values are paired layers,
not the old scalar result. Use `by_market[market]` for a single-market result,
or `by_market_key["research_id|JC"]`. External consumers of the old scalar shape
must switch to these paths. Python queries and CLI require an explicit market.
Legacy v2 indexes are read through their daily manifests without trusting
previously collapsed labels. Manual labels/screenshots must specify
`source_market`; unspecified-market evidence is retained but not auto-applied.

MODEL_1 feature packets automatically query both markets by Titan ID:

| JC | BD | Teacher reference |
|---|---|---|
| 1 | 1 | STRONG_EXCLUDE |
| 1 | 0 | EXCLUDE, BD counterevidence |
| 0 | 1 | NO_EXCLUSION_SIGNAL, BD risk hint |
| 0 | 0 | NO_EXCLUSION_SIGNAL |
| UNKNOWN | any | UNKNOWN, BD never substitutes for JC |

JC is PRIMARY_LAYER; BD is SECONDARY_VALIDATION_LAYER. These are teacher
reference signals; the independent student analysis and decision math remain
separate. Existing packet arguments and fields remain supported.

## Upgrade and separate evaluation

```bash
python -m draw_exclusion.migrate_markets
python -m draw_exclusion.statistics
```

Rebuild historical indexes once. Migration backs up an existing SQLite database,
adds views, and regenerates only derived index/latest files. Raw HTML, frozen
version manifests and historical labels are not rewritten. Existing compound
database keys and all Titan mappings remain unchanged. The daily runner also
upgrades an old index even when the website hash is unchanged.

Statistics freeze the first observed pre-kickoff label separately for each
market, count each fixture/market once, and exclude missing/conflicting outcomes
from accuracy denominators. JC and BD exclusion hit rates and both disagreement
groups are reported independently. “Leading” means one market excludes while
the other does not (not chronological precedence). An actual draw is the
exclusion failure type; NOT_EXCLUDED is not treated as predicting a draw.
No final outcomes are inferred or fetched by this layer.
