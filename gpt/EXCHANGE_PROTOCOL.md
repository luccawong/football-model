# Betfair Exchange Layer Protocol — GPT-EXCHANGE-1.0.0

## Purpose
Use Betfair Exchange as a conditional microstructure/price-discovery evidence layer. It is not an automatic smart-money oracle and cannot issue a ticket.

## Production provider
Primary provider: **OddsPapi v4** at `https://api.oddspapi.io/v4`.

- Football `sportId=10`.
- Betfair Exchange bookmaker slug: `betfair-ex`.
- Full-time 1X2 is canonical market `101`, outcomes `101=home`, `102=draw`, `103=away`.
- `/v4/account` is used for credential/quota health checks because it is unmetered.
- `/v4/fixtures` discovers/matches the football fixture.
- `/v4/odds?fixtureId=...&bookmakers=betfair-ex&verbosity=3` supplies the current exchange-backed odds payload.
- `/v4/historical-odds` may later support historical reconstruction without consuming normal request quota.

## v4 exchange data contract
For each standard selection, preserve exactly what OddsPapi returns:
- `price`;
- `limit`;
- `bookmakerChangedAt`;
- `changedAt`;
- `exchangeMeta` raw;
- bookmaker/market suspended-active state when available.

`exchangeMeta` is provider-specific (`any|null`) and may contain exchange information such as liquidity or lay price. Its internal structure must be inspected from real Betfair responses before fields are promoted to stable model features. Do not assume the richer v5 `meta.back[]/meta.lay[]` schema exists in v4.

## Derived evidence
Always available when prices exist:
- exchange price/implied probability;
- price movement across our own saved snapshots;
- closest-same-time Exchange-vs-bookmaker probability divergence.

Conditional on verified `exchangeMeta` fields:
- Back/Lay spread;
- available liquidity/size;
- order-book depth;
- order-book imbalance.

## Fields that must not be fabricated
Unless the actual v4 payload explicitly provides them, keep these `MISSING`:
- market `total_matched`;
- traded ladder / matched-volume buckets;
- traded-volume velocity;
- guaranteed multi-level Back/Lay ladders.
`limit` is not matched volume.

## Timestamp discipline
Preserve separately:
1. `bookmakerChangedAt` — source/bookmaker timestamp when supplied;
2. `changedAt` — OddsPapi recorded-change timestamp;
3. our ingestion timestamp.
Do not claim second-level exchange lead/lag if provider latency is not accounted for.

## Quota discipline
- Empty/inactive watchlist: make no billable odds call.
- Do not repeatedly fetch static market definitions in the scheduled collector; canonical football 1X2 IDs are versioned in config/code.
- Prefer fixture batching/filtering over many discovery requests.
- Health checks use unmetered `/v4/account`.
- Polling cadence must reflect the user's request allowance.

## Hard interpretation rules
- Exchange activity is not labelled informed/smart money without validated evidence.
- High available size or limit alone is not a direction.
- Back/Lay imbalance alone is not a direction.
- A price move without liquidity context is weaker evidence.
- Bookmaker-vs-exchange comparisons require the closest same-time slice.
- Missing Betfair data is `MISSING`, not evidence against either side.
- In-play data must not contaminate pre-match opening/closing analysis.
- Order placement, staking and execution remain RESEARCH_ONLY.

## Future upgrade path
OddsPapi v5 B2B/WebSocket can be added later if the account is upgraded and richer guaranteed exchange ladders are required. Direct Betfair tooling (`betfairlightweight`, `betfairutil`, `flumine`) remains optional research/infrastructure rather than a requirement for the pre-match GPT model.
