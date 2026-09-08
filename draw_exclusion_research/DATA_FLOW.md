# DATA FLOW

```text
External draw-exclusion website
              │  immutable GET + HTTP metadata
              ▼
Raw snapshot manager ───────► raw HTML + SHA-256 + content version
              │
              ▼
Label parser ───────────────► JC/BD positive and control rows
              │               stable research_match_id
              ▼
Deterministic match resolver
              │  exact names / controlled aliases; no fuzzy guessing
              ▼
Existing football-model / Titan validation packets
              │  normalized bookmaker identity
              │  full 1X2 / AH / OU timeline
              ▼
SQLite research store
       ┌──────┴──────────┐
       │                 │
       ▼                 ▼
Feature snapshots     Final results (Truth only)
       │                 │
       └──────┬──────────┘
              ▼
Versioned research dataset
              │
       ┌──────┴──────────┐
       ▼                 ▼
Teacher imitation    Teacher effectiveness
Website label        Non-draw/draw outcome
       │                 │
       └──────┬──────────┘
              ▼
Future Draw Exclusion Layer
KEEP_DRAW / WEAK_EXCLUDE / EXCLUDE / STRONG_EXCLUDE
```

## Time and leakage boundaries

1. Website label is frozen at `website_snapshots.snapshot_time_utc`.
2. Later website versions create new snapshot rows; they never mutate an earlier label.
3. External odds are raw events. A feature snapshot may only read events whose `odds_time <= feature_time`.
4. Feature time must be earlier than kickoff; recommended targets are T-24h, T-12h, T-6h, T-3h, T-1h and T-30m.
5. `final_results` is a separate Truth layer and may only be joined for evaluation/training target construction, never for feature generation.
6. 竞彩与北单 remain separate strata through labels, reports and evaluation.

## Same-time slices

The repository already supplies `src.timeline.slices.synchronize`, with explicit time gaps and lookahead flags. When current external data becomes available, the research feature builder will construct both ±5-minute and ±10-minute slices. A quote outside the selected window will not enter cross-company differences.

## Failure behavior

- Label payload shape change: parsing fails closed; raw HTML remains preserved.
- Missing row field: parsing fails closed; no partial database snapshot is published.
- Titan no match: website row is retained with `not_found`.
- Titan ambiguity: all candidates are recorded; no ID is chosen.
- Missing market: NULL/0 coverage is reported, never imputed silently.
- Same-day website change: new content version plus row-level diff; old version remains intact.
