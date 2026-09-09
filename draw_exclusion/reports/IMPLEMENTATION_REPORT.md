# External Draw Exclusion Label Layer — Implementation Report

## CREATED

- Formal `draw_exclusion/` package with stable crawler imports, immutable snapshot manager, canonical alias registry, conservative resolver, daily manifest builder, cross-run diff, QC, fast index, query CLI, database extensions, provenance files, and forensic evidence folders.
- GitHub Actions workflow `.github/workflows/draw-exclusion-daily.yml`.
- Formal label-layer tests in `tests/test_external_draw_label.py`.
- Daily 2026-09-09 manifest, immutable capture manifests, `latest.json`, `index.json`, and QC report.

## MODIFIED

- `scripts/run_draw_exclusion_daily.py` now invokes the formal layer.
- The active source URL was replaced with the credential-free EdgeOne root URL.
- `requirements.txt`, `.gitignore`, and the repository README were updated.

## REUSED

- Audited static HTML collector and parser.
- Existing SHA/diff persistence concepts and SQLite base schema.
- Existing Titan packet adapter and validated match resolver.
- Existing normalization and odds-line utilities.

## TEST RESULTS

- `python -m unittest discover -s tests -p "test*.py"`: 63 passed.
- Daily QC invariants: PASS.
- SQLite foreign-key check: no violations.
- Exact canonical fixture query: verified.
- Missing snapshot and out-of-pool queries: verified as `NULL`, never `0`.

## TODAY SAMPLE — 2026-09-09

| Pool | Total | EXCLUDED | NOT_EXCLUDED |
|---|---:|---:|---:|
| 竞彩 | 10 | 4 | 6 |
| 北单 | 58 | 9 | 49 |

Snapshot SHA-256: `0069284f60d0d759535f8dc1e37e240f5ba92a29566ac57f01be4a00885f542e`.

## MATCHING

- Titan matched: 0
- Titan unmatched: 68
- Fuzzy auto-matches: 0
- Duplicate rows: 0
- Label/forensic conflicts: 0
- Unregistered alias pairs: 66 (deterministic fallback IDs retained; no unsafe fuzzy links)

The current Titan validation packets do not contain these fixtures. The
crosswalk table and fast Titan index are active and populate automatically when
matching Titan packets are present.

## AUTOMATION

The workflow is configured for 17:10 and 18:10 Beijing time plus manual
dispatch. It refuses to promote a daily label when the page-reported date is
stale. Derived JSON/index/QC files are committed. Raw HTML and SQLite are stored
as private 30-day artifacts instead of Git history because the HTML contains
access-gate code.

## HOW CHATGPT SHOULD QUERY IT

1. Read `draw_exclusion/index.json`.
2. If Titan ID exists in `by_titan_match_id`, use that entry.
3. Otherwise run `python draw_exclusion/query_label.py --date DATE --league LEAGUE --home HOME --away AWAY --kickoff HH:MM`.
4. Treat only `MATCHED_EXCLUDED` as `1` and `MATCHED_NOT_EXCLUDED` as `0`.
5. Treat every missing, stale, ambiguous, or failed status as `NULL / UNKNOWN`.
6. Keep this Teacher label separate from the independent Draw Exclusion model.

