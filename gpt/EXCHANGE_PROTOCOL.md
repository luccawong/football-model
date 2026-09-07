# Betfair Exchange Layer Protocol — GPT-EXCHANGE-1.0.0

## Purpose
Use Betfair Exchange as a conditional microstructure/price-discovery evidence layer. It is not an automatic smart-money oracle and cannot issue a ticket.

## Production provider now
Primary live provider: **The Odds API** in `EXCHANGE_LITE` mode.

Current Betfair exchange bookmaker keys:
- `betfair_ex_uk`
- `betfair_ex_eu`
- `betfair_ex_au`

Current provider markets:
- `h2h` = Back side
- `h2h_lay` = Lay side

Request bet limits when available with `includeBetLimits=true`.

## Available production inputs
1. Exact event mapping to the Titan football match.
2. Prematch event and bookmaker timestamps.
3. Match Odds Back prices for home/draw/away.
4. Match Odds Lay prices for home/draw/away.
5. Bet limits where returned by the provider.
6. Same-time bookmaker snapshot for cross-venue divergence.

## Exchange Lite derived evidence
- Best Back and Lay prices.
- Raw and Betfair-tick Back/Lay spread.
- Back/Lay implied probability interval and midpoint.
- Exchange normalized 1X2 probability estimate.
- Bet-limit asymmetry as liquidity context only.
- Price velocity from our own saved chronological snapshots.
- Exchange-vs-bookmaker percentage-point divergence.

## Explicitly unavailable in Exchange Lite
Do not fabricate or infer these from bet limits:
- full multi-level order-book depth;
- multi-level order-book imbalance;
- market total matched;
- traded ladder / individual traded-volume buckets;
- traded-volume velocity.
These remain `MISSING` until a deeper Betfair feed is connected.

## Optional deeper stack later
- `betcode-org/betfair` (`betfairlightweight`): API-NG, market streaming, historical stream parsing.
- `mberk/betfairutil`: historical prices-file analytics and book percentage.
- `betcode-org/flumine`: replay/simulation/execution framework. Execution remains RESEARCH_ONLY.

## Hard interpretation rules
- Exchange flow is not labelled informed/smart money without validated evidence.
- A lower Back price alone is not a direction.
- Bet limit alone is not a direction and is not equivalent to matched volume.
- Bookmaker-vs-exchange comparisons require the closest same-time slice.
- Provider `last_update` must be preserved; our ingestion timestamp must be recorded separately.
- Missing Betfair data is `MISSING`, not evidence against either side.
- In-play data must not contaminate pre-match analysis.
- Order placement, staking and execution remain RESEARCH_ONLY and separate from direction modelling.
