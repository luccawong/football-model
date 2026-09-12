# JC / BD market isolation acceptance

Implementation and local historical-index migration completed 2026-09-12.
Pre-publication validation also integrates the default branch's Stage14 updates
and 2026-09-11 data. The publication commit uses
`feat: separate JC and BD draw exclusion markets`.

## Files

| File | Change |
|---|---|
| draw_exclusion/markets.py | New market keys, explicit layer fields, MODEL_1 reference mapping |
| draw_exclusion/matcher.py | Mandatory market filter, market-scoped result identity |
| draw_exclusion/query_label.py | Mandatory market for Titan/fixture/CLI; scoped manual evidence; v2 read adapter |
| draw_exclusion/indexer.py | v3 market and paired-layer indexes, independent ambiguity handling |
| draw_exclusion/crawler/build_daily_manifest.py | Independent JC_layer / BD_layer fields and market_key |
| draw_exclusion/crawler/qc.py | Same-market conflict detection |
| draw_exclusion/database/schema.sql | JC and BD evidence views over existing market compound keys |
| draw_exclusion/database/repository.py | Re-observation preserves stored student decisions and outcomes |
| draw_exclusion/run_daily.py | Upgrade old indexes even on unchanged website hash |
| draw_exclusion/statistics.py | Separate exclusion hit rates and both disagreement cohorts |
| draw_exclusion/migrate_markets.py | Backup SQLite, add views, rebuild historical indexes |
| draw_exclusion/index.json | Regenerated schema 3.0, JC 58 / BD 370 fixture-market entries |
| gpt/model_1_packet_bridge.py | Separate automatic Titan queries and JC-primary reference packet |
| config/active_decision_policy.json | JC execution scope; BD validation-only policy |
| gpt/FOOTBALL_SOP.md | Explicit JC/BD query and execution scope |
| gpt/FOOTBALL_CANONICAL_MEMORY.md | Explicit JC/BD roles and four-case rules |
| draw_exclusion/README.md | API, migration, statistics, compatibility documentation |
| tests/test_external_draw_label.py | Existing calls specify market |
| tests/test_draw_markets.py | 12 new isolation, migration, database, statistics and crawler tests |
| .github/workflows/draw-exclusion-daily.yml | Include new draw-layer tests |
| draw_exclusion/reports/MARKET_ISOLATION_REPORT.md | This report |

Pre-existing local 2026-09-12 daily/version/QC files were preserved. latest.json
retains the same pointer shape and local latest date 2026-09-12.

## Data and compatibility

Keep research_match_id as the stable fixture identity and preserve Titan
crosswalks. Use research_match_id|JC and research_match_id|BD as separate label
keys. Existing SQLite label/evaluation compound keys already include market;
the old generic scalar columns are compatibility fields within market-scoped
records, never a fixture-wide combined label.

Both layers expose their own prefixed draw_exclusion_label, status, snapshot_id,
snapshot_time, source and provenance. Missing evidence is null, never 0.
Same-market conflicts remain ambiguous; opposite JC/BD labels do not.

Query examples:

```bash
python draw_exclusion/query_label.py --market JC --match-id 3049507
python draw_exclusion/query_label.py --market BD --match-id 3049507
```

Machine paths:

- index.by_market.JC.by_titan_match_id[id]
- index.by_market.BD.by_titan_match_id[id]
- index.by_market_key[research_match_id + "|JC"]
- index.by_titan_match_id[id].JC_layer / BD_layer

Consumers expecting the old scalar at by_titan_match_id[id] must adopt a market
path. A missing market argument is rejected. Existing v2 evidence is readable
through the adapter; historical indexes must be rebuilt once.

## MODEL_1 and statistics

JC=1/BD=1: STRONG_EXCLUDE reference.
JC=1/BD=0: EXCLUDE reference and BD counterevidence.
JC=0/BD=1: no exclusion, BD risk hint.
JC=0/BD=0: no exclusion signal.
JC missing: UNKNOWN, without BD fallback.

Statistics freeze the first pre-kickoff observation per fixture and market.
Repeated snapshots do not multiply sample counts. Actual draws are exclusion
failures. Missing/conflicting outcomes are excluded from hit-rate denominators.
JC-leading and BD-leading mean opposing labels, not chronological precedence.
Current database has no evaluated outcomes; accuracy remains null.

## Validation

- Full project after default-branch integration: 135 passed, 0 failed.
- JC/BD conflict and isolation suite: 12 passed, 0 failed.
- MODEL_1 bridge suite: 4 passed, 0 failed.
- Workflow draw-layer unittest selection: 26 passed, 0 failed.
- Four required opposite-label/single-market cases: passed.
- Packet bridge, v2 index recovery, explicit-market guard, manual isolation,
  same-market ambiguity, statistics, unchanged-hash daily runner: passed.
- Integrated migration: JC 58 / BD 370 indexed fixture-market records.
- SQLite foreign_key_check: 0 violations.
- 15 historical HTML/daily/version evidence files checked: 0 changed hashes.
- SQLite backed up before adding market views.
- git diff --check: passed.
