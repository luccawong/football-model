# Changelog

## MODEL_1 SOP-1.5 / SOURCE-POLICY-1.1 / MEMORY-SAFEGUARDS — 2026-09-09
- Added explicit analysis-depth rule: one match preferred, two practical maximum before compression risk; multi-match H1/Red Team remain independent.
- Added opening reasonable-band + adjacent counterfactual pricing requirement and clarified market-intent/inducement as inference rather than fact.
- Added rating safeguards: generic risk alone does not justify downgrade; downgrade requires material pricing/path/cross-market/cover-ceiling/data-integrity counterevidence; do not upgrade beyond observed market ceiling without stable deeper consensus.
- Added price/execution safeguard under the new no-PASS regime: a materially different available line requires re-audit and a current formal main, not silent grade transfer or legacy price-threshold PASS.
- Added explicit missing-data impact disclosure and no timeline interpolation.
- Added `config/model_1_source_policy.json`: Titan is the raw odds authority when the user supplies a Titan packet; Aoke is supplemental cross-check only; OddsPapi is genuine Betfair Exchange Shadow; API-Football remains a separate software-provider layer where configured.
- Added raw-packet/storage rules: preserve match_id, source/timestamps/parser version/raw evidence/QC, multi-match `match_index`, per-match isolation, lineup image/DOM capture, validation-packet retention and `validation_packets/latest.json` pointer.
- Added historical JCB goal-count/HTFT memory under `research/jcb/` as research-only, with no automatic production authority.
- Strengthened forward validation: frozen-ticket/score recovery cannot be reconstructed from results; identity-conflicted samples stay outside formal hit-rate statistics; Top1 vs Top3 score metrics remain separate; HELPFUL/HARMFUL labels require a frozen pre-match action and confirmed settlement.

## MODEL_1 TRACE / MEMORY-GAP / FORWARD-VALIDATION — 2026-09-09
- Added `config/model_1_trace_contract.json` and `gpt/formal_trace.py` so every full MODEL_1 analysis can be serialized and validated as an 18-stage pre-match trace.
- Added `gpt/model_1_packet_bridge.py` to map existing Quant/Feature outputs into MODEL_1 stage evidence without modifying validated mathematical formulas merely for orchestration.
- Added tests for the trace engine and packet bridge.
- Added `gpt/MEMORY_GAP_AUDIT_2026-09-09.md` after a cross-chat memory review; captured missing surrounding controls such as depth-over-batch-size, market-intent/counterfactual opening interpretation, price-vs-direction separation, missing-timeline disclosure, prospective sampling nodes, candidate provenance, result-confirmation/settlement discipline, JC-vs-BD draw-model-family separation, model-stability freeze discipline and legacy provider/JCB conflicts.
- Added `research/underdog_outright/RESEARCH_PROTOCOL.md` for historical weak-side outright residual/divergence research with no formal ticket authority until validated.
- Added `draw_exclusion_research/MODEL_FAMILY_PROTOCOL.md` separating `JC_DRAW_MODEL` and `BD_DRAW_MODEL` research families.
- Added `validation/MODEL_1_FORWARD_VALIDATION.md` with candidate provenance, T-5h/T-2h/T-1h/T-30m/T-10m intended collection nodes, pre-match freeze, real result confirmation and objective quarter-line settlement rules.
- Added `config/model_1_supporting_contracts.json`; updated MODEL_1 profile, Runtime and Manifest to load the new contracts while keeping research/legacy material outside formal decision authority.

## MODEL_1 DEFAULT / GPT-FOOTBALL-SOP-1.4 / DECISION-ENGINE-1.0.0 — 2026-09-09
- Registered the current football stack as `MODEL_1`, the repository default model, via `config/model_registry.json` and `models/MODEL_1_DEFAULT.md`.
- Added future-model isolation: if MODEL_1 performance is later unsatisfactory, freeze it and create MODEL_2/3/etc rather than overwriting MODEL_1 history.
- Reordered the full SOP to the user-approved 18-stage sequence with **fundamentals first**.
- Fundamentals now explicitly require recent match-by-match review, opponent-quality context, how wins/losses happened, and future schedule/priority pressure; arbitrary numeric opponent weights remain forbidden until calibrated.
- Added mandatory post-fundamentals **实开/韬开** diagnostic inside the 1X2 stage; it is a prior/diagnostic, not a mechanical result rule.
- Added mandatory 1X2 -> AH **欧亚转换** consistency audit before accepting an Asian-handicap interpretation.
- Moved market attraction ahead of draw-exclusion and underdog-outright decisions.
- Draw-exclusion `EXCLUDED=1` now explicitly opens an immediate HOME-vs-AWAY winner audit; `NOT_EXCLUDED=0` keeps the enhanced draw audit.
- Kept mandatory underdog outright audit after the draw branch, including favourites -0.75 and deeper.
- Correct-score stage explicitly uses repository Poisson/Dixon-Coles + Bayesian/context framework and direction-consistency gate.
- Implemented second-step machine enforcement:
  - updated `config/active_decision_policy.json` with MODEL_1 and the exact 18-stage order;
  - updated `config/module_registry.json` with stage mapping and new modules;
  - added `gpt/decision_engine.py` to validate stage order, draw branch, underdog gate, Red Team verdict and exactly-one-main output;
  - added `tests/test_decision_engine.py`;
  - updated `gpt/GPT_RUNTIME.md`, `gpt/FULL_STACK_PROTOCOL.md`, `gpt/MANIFEST.json`, `config/full_stack_config.json`, `gpt/FOOTBALL_CANONICAL_MEMORY.md` and `gpt/FOOTBALL_SOP.md`.

## GPT-FOOTBALL-SOP-1.3 / CANONICAL-MEMORY-2026-09-09 — 2026-09-09
- Migrated active cross-chat football-model rules into `gpt/FOOTBALL_CANONICAL_MEMORY.md` for user audit and future runtime loading.
- Added machine-readable `config/active_decision_policy.json`.
- Replaced the legacy formal-main/non-main/PASS output policy with the newest rule: exactly one formal main ticket per fully analysed match, no non-main tickets, no final PASS; uncertainty is expressed through grade and execution conditions.
- Formalized the one-month draw-exclusion execution test: `EXCLUDED=1` is a hard draw-removal constraint; `NOT_EXCLUDED=0` triggers enhanced mandatory draw audit; missing/unknown stays UNKNOWN.
- Formalized mandatory underdog outright audit for favourites -0.75 and deeper, including same-time-slice company divergence and U0-U3 evidence grading.
- Preserved Betfair/OddsPapi as SHADOW_RESEARCH with zero formal-system impact.
- Added an explicit conflict-review section for JCB/Sporttery scope, emergency data-integrity handling under no-PASS, and whether exactly-one-main applies to quick-scan candidates or only full analysis.

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
