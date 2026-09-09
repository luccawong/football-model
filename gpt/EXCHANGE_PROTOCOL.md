# Betfair Exchange Layer Protocol — GPT-EXCHANGE-1.1.0

## Purpose
Use Betfair Exchange as a conditional microstructure/price-discovery evidence layer. It is not an automatic smart-money oracle and cannot issue a formal ticket by itself.

Current integration mode: **SHADOW_RESEARCH**. Exchange outputs are tested separately from the formal football system and are excluded from formal-system win-rate statistics until validated.

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

Validated live OddsPapi v4 `exchangeMeta` responses may include:
- `availableToBack[]` with price/size;
- `availableToLay[]` with price/size;
- runner-level `tradedVolume`;
- `betDelay`.

Preserve the raw payload before promotion. A field is only promoted after it has been observed and validated in real `betfair-ex` responses.

## Derived evidence
Always available when prices exist:
- exchange price/implied probability;
- price movement across our own saved snapshots;
- closest-same-time Exchange-vs-bookmaker probability divergence.

Conditional on verified `exchangeMeta` fields:
- Back/Lay spread;
- available liquidity/size;
- multi-level Back/Lay depth when actually returned;
- order-book imbalance;
- runner traded-volume change across our own saved snapshots.

## Fields that must not be fabricated
Unless the actual payload explicitly provides them, keep these `MISSING`:
- market `total_matched`;
- traded ladder / matched-volume buckets;
- matched-trade side direction;
- any field inferred only from a screenshot rule but not supported by current feed.

`limit` is not matched volume. Runner `tradedVolume` is not the same thing as side-specific matched flow.

## Shadow rulebook
Canonical rulebook: `config/exchange_rulebook.json`.
Executable evaluator: `gpt/exchange_shadow_rules.py`.

The current user-supplied rulebook contains two source sections:
- `3.2 必发/市场深度数据`;
- `3.3 庄家操纵/市场博弈`.

Runtime discipline:
1. Freeze the non-Exchange Baseline first.
2. Load and evaluate every rule in `exchange_rulebook.json` through the shadow-rule evaluator.
3. Each rule must be emitted as `TRIGGERED`, `NOT_TRIGGERED`, `MISSING`, `UNRESOLVED`, or `CONFLICT` with the exact inputs used.
4. Missing required input means `MISSING`, never `false`.
5. A threshold/definition not present in the source screenshot means `UNRESOLVED`; do not invent it.
6. Red-marker source rules are priority review flags, not automatic overrides.
7. Exchange Shadow output is compared against the frozen Baseline and settled separately after the match.
8. Shadow results do not enter formal main/non-main statistics.

### Rule-source fidelity safeguards
- After the supplementary screenshot, section 3.2 visibly contains **11** rules: R61, R62, R63, R64, R65, R66, R67, R74, R75, R76 and R77, although the source header still says “10条”. Preserve all 11 visible rules and flag the count conflict; do not delete a rule just to make the header count fit.
- R61 says the three profit/loss ratios should be “close” but gives no numeric tolerance, so automatic triggering remains `UNRESOLVED` until a threshold is supplied.
- R96 and R99 mention “三条件” but the screenshots do not enumerate those conditions. They remain `UNRESOLVED`.
- Terms such as `诱盘`, `庄家控盘`, `操纵`, `隐藏力`, and `大资金看好` are preserved as source-rule labels. They must be treated as hypotheses/heuristic labels, not verified factual claims without independent evidence.

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
- A single Exchange rule cannot create or overturn a formal-system ticket during shadow testing.
- Order placement, staking and execution remain RESEARCH_ONLY.

## Future promotion gate
Do not promote Exchange Shadow into the formal decision stack until the separate test sample shows reproducible incremental value, including at minimum:
- Baseline wrong → Exchange corrected;
- Baseline right → Exchange led wrong;
- Baseline wrong → Exchange reinforced wrong;
- Baseline right → Exchange reinforced right;
- performance by Exchange-vs-bookmaker divergence bands;
- performance by rule family and competition/market regime.

## Future upgrade path
OddsPapi v5 B2B/WebSocket can be added later if the account is upgraded and richer guaranteed exchange ladders are required. Direct Betfair tooling (`betfairlightweight`, `betfairutil`, `flumine`) remains optional research/infrastructure rather than a requirement for the pre-match GPT model.
