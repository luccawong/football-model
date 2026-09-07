# Betfair Exchange Layer Protocol — GPT-EXCHANGE-1.0.0

## Purpose
Use Betfair Exchange as a conditional microstructure/price-discovery evidence layer. It is not an automatic smart-money oracle and cannot issue a ticket.

## Preferred open-source stack
- `betcode-org/betfair` (`betfairlightweight`): API-NG, market streaming, historical stream parsing.
- `mberk/betfairutil`: historical prices-file analytics, book percentage, CSV/data-frame utilities.
- `betcode-org/flumine`: historical replay/simulation and paper/live execution framework. Execution features remain RESEARCH_ONLY for the GPT pre-match model.

## Required live/historical inputs
1. Exact event/market mapping to the football match.
2. Prematch market state and timestamps.
3. For each Match Odds runner: best Back, best Lay, available sizes for configured ladder levels.
4. Market `total_matched`; `EX_TRADED`/traded ladder when available.
5. Same-time bookmaker snapshot for cross-venue divergence.

## Derived evidence
- Back/Lay spread in raw odds and Betfair ticks.
- Back/Lay book percentages.
- Order-book depth and descriptive imbalance.
- Total matched and matched-volume velocity.
- Price/implied-probability velocity.
- Exchange normalized probabilities.
- Betfair-vs-bookmaker percentage-point divergence.

## Hard interpretation rules
- Exchange flow is not labelled informed/smart money without validated evidence.
- High matched volume alone is not a direction.
- Back/Lay imbalance alone is not a direction.
- A price move without liquidity context is weaker evidence.
- Bookmaker-vs-exchange comparisons require the closest same-time slice.
- Missing Betfair data is `MISSING`, not evidence against either side.
- In-play data must not contaminate a pre-match opening/closing analysis.
- Order placement, staking and execution strategies are RESEARCH_ONLY and are separate from direction modelling.
