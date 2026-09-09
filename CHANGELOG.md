# Changelog

## GPT-EXCHANGE-1.1.0 / BETFAIR-SHADOW-RULES-1.0.0 — 2026-09-08
- Switched the current Betfair integration into SHADOW_RESEARCH mode for a multi-day isolated test; Shadow results are excluded from formal football-system statistics.
- Added `config/exchange_rulebook.json` from the user-supplied Betfair/depth and market-game screenshots.
- Added executable evaluator `gpt/exchange_shadow_rules.py` and CI tests in `tests/test_exchange_shadow_rules.py`.
- Added R61 `盈亏比均衡=市场成熟` and R62 `高概率低凯利=核心` from the supplementary screenshot.
- Preserved all visible section 3.2 rules. The merged screenshots show 11 visible rules (R61,R62,R63,R64,R65,R66,R67,R74,R75,R76,R77) although the source header says 10; this is stored as a source-count QC conflict rather than deleting a rule.
- R61 remains UNRESOLVED for automatic triggering because the source says the three profit/loss ratios should be “close” without defining a numeric tolerance.
- R96/R99 remain UNRESOLVED because their referenced three validation conditions are not shown in the supplied screenshots.
- Added deterministic states TRIGGERED / NOT_TRIGGERED / MISSING / UNRESOLVED / CONFLICT so absent inputs and undefined thresholds cannot be silently treated as negative signals.
- Added measurable implementations for R62, R63, R66, R74, R76, R36, R38, R39 and R58 where the source provides enough structure; subjective/undefined rules remain guarded.
- Updated Runtime to freeze the non-Exchange Baseline first, then run Exchange Shadow and classify its incremental effect separately.
- Updated OddsPapi v4 contract to recognize validated `availableToBack`, `availableToLay`, runner `tradedVolume` and `betDelay` when actually returned, while still forbidding fabrication of matched-side flow or market total matched.

## Exchange Bridge 1.2.0 — 2026-09-07
- Corrected production provider to OddsPapi v4 for the user's existing account/API key.
- Pinned REST base to `https://api.oddspapi.io/v4` and Betfair Exchange slug to `betfair-ex`.
- Added unmetered `/v4/account` credential/subscription smoke test; confirmed the configured account is active with football and `betfair-ex` access.
- Switched fixture discovery to `/v4/fixtures` and current Betfair data to `/v4/odds`.
- Preserves `price`, `limit`, `bookmakerChangedAt`, `changedAt`, and raw `exchangeMeta` without assuming an undocumented exchange-meta shape.
- Uses canonical football full-time 1X2 market/outcome IDs (101 / 101-102-103) in scheduled collection to avoid repeatedly spending quota on static `/markets` calls.
- Keeps `total_matched`, traded ladders, traded-volume velocity and guaranteed multi-level depth MISSING unless explicitly returned.
- Retains `THE_ODDS_API_KEY` only as a backwards-compatible GitHub Secret alias; canonical future secret name is `ODDSPAPI_API_KEY`.

## GPT-FOOTBALL-FULLSTACK-1.1.0 — 2026-09-07
- Added conditional Betfair Exchange layer `GPT-EXCHANGE-1.0.0`.
- Added deterministic Back/Lay spread in Betfair ticks, book percentage, depth/imbalance, matched-volume velocity, price velocity and exchange-vs-bookmaker divergence utilities.
- Registered Betfair market mapping, microstructure, liquidity, same-time cross-venue comparison and historical replay modules.
- Added anti-double-counting groups for exchange microstructure and exchange liquidity.
- Explicitly blocked the shortcuts “Betfair = smart money”, “high matched volume = direction”, and “order-book imbalance = direction”.
- Registered betfairlightweight, betfairutil and flumine as the preferred open-source Betfair stack; order execution remains RESEARCH_ONLY.

## GPT-FOOTBALL-FULLSTACK-1.0.0 — 2026-09-07
- Added exhaustive registry-driven football stack to stop ad-hoc module additions.
- Added GPT-FEATURE-1.0.0: disagreement/entropy, Brier/RPS/log loss, calibration bins, AH failed-upgrade/reversal, probability lifecycle, source freshness, module gating and schedule flags.
- Added anti-double-counting groups across strength, squad, market, chance creation, schedule and narrative evidence.
- Added conditional Elo/Pi/ClubElo, xG/npxG/xGA, finishing/goalkeeper/set-piece, squad value/expected minutes, xT/VAEP, travel/weather/referee and relationship-network modules.
- Added explicit ACTIVE/PARTIAL/MISSING/STALE/CONFLICT/RESEARCH_ONLY states.
- Blocked stale Transfermarkt-datasets rows from live 2026/27 use until freshness recovers.
- Added open-source registry for penaltyblog, soccerdata, transfermarkt-datasets, socceraction, kloppy and StatsBomb workflows.
- Added calibration/walk-forward/OOD layer while preserving Red Team + ticket lock rules.

## GPT-QUANT-0.1.0 — 2026-09-07
- Initial deterministic de-vig, Dixon-Coles, market-implied goal reconstruction, AH/OU settlement grid and Quant Packet validation.
