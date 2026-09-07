# Changelog

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
