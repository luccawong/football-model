# Betfair Exchange Layer Protocol — GPT-EXCHANGE-1.0.0

## Purpose
Use Betfair Exchange as a conditional microstructure/price-discovery evidence layer. It is not an automatic smart-money oracle and cannot issue a ticket.

## Production provider
Primary provider: **OddsPapi v5**.

OddsPapi is used in two complementary modes:
1. REST snapshots for on-demand pre-match collection (`/fixtures`, `/markets`, `/fixtures/odds`).
2. WebSocket streaming as an optional later enhancement for lower-latency continuous updates.

Football uses `sportId=10`. Fixture matching is based on team names + kickoff time, with optional pinned `provider_fixture_id` after a successful mapping.

## Betfair data carried from OddsPapi
For exchange/prediction-market bookmakers, OddsPapi may expose in each odds outcome:
- `price`;
- `limit`;
- `bookmakerChangedAt`;
- `changedAt`;
- `meta.back[]` price/size ladder;
- `meta.lay[]` price/size ladder.
Bookmaker metadata such as `staleOdds`, `suspended`, `hasOdds`, and `updatedAt` must also be preserved when returned.

## Derived evidence
- Best Back and best Lay.
- Back/Lay spread in raw odds and Betfair ticks.
- Multi-level order-book depth when present.
- Descriptive order-book imbalance when present.
- Back/Lay implied-probability interval and midpoint.
- Exchange normalized 1X2 probability estimate.
- Price and liquidity changes from saved chronological snapshots.
- Exchange-vs-bookmaker percentage-point divergence at the closest same-time slice.

## Fields that must not be fabricated
Unless OddsPapi explicitly returns them, keep the following `MISSING`:
- market `total_matched`;
- traded ladder / traded-volume buckets;
- traded-volume velocity.
`limit` and available size-at-price are liquidity context, not matched volume.

## Timestamp discipline
Preserve all three when available:
1. `bookmakerChangedAt` — bookmaker/exchange source timestamp;
2. `changedAt` — OddsPapi gateway timestamp;
3. our ingestion timestamp.
Do not claim second-level Exchange lead/lag versus another bookmaker if provider latency is not accounted for.

## Hard interpretation rules
- Exchange activity is not labelled informed/smart money without validated evidence.
- High available size alone is not a direction.
- Back/Lay imbalance alone is not a direction.
- A price move without liquidity context is weaker evidence.
- `staleOdds=true` is a QC warning/gate, not usable directional evidence.
- Bookmaker-vs-exchange comparisons require the closest same-time slice.
- Missing Betfair data is `MISSING`, not evidence against either side.
- In-play data must not contaminate pre-match opening/closing analysis.
- Order placement, staking and execution remain RESEARCH_ONLY.

## Reference/deeper tooling
Direct Betfair tooling remains optional rather than required:
- `betcode-org/betfair` (`betfairlightweight`);
- `mberk/betfairutil`;
- `betcode-org/flumine` for replay/simulation/execution research.
