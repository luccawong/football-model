# GPT Runtime Contract — Full Stack 1.3

This repository is the persistent cross-chat source of truth for the GPT football analysis stack, not a standalone web application.

## Full-SOP trigger
When the user supplies football match data and requests the full SOP with independent Red Team review, automatically execute the current repository stack without requiring the user to name individual modules.

## Current Betfair mode
Betfair/OddsPapi is currently in **SHADOW_RESEARCH** mode for a multi-day test. It must be evaluated separately from the formal football system.

Hard separation:
- Freeze the formal/non-Exchange Baseline before looking at Betfair Shadow conclusions.
- Betfair Shadow results are stored and settled separately.
- Betfair Shadow results do not enter formal main-ticket, non-main-ticket or formal model win-rate statistics.
- Betfair Shadow may be compared with Baseline for correction/harm analysis, but cannot silently rewrite the frozen Baseline.

## Fixed cross-chat order
1. Read MANIFEST, quant/full-stack/exchange configs, rulebook and module registry.
2. Parse Titan input preserving match ID/state, timestamps, company identity, MAIN/ALT, raw prices and QC.
3. Build module states: ACTIVE/PARTIAL/MISSING/STALE/CONFLICT/RESEARCH_ONLY; never silently omit a registered module.
4. Run snapshot/freshness/identity/same-time/conflict QC.
5. Run GPT-QUANT and freeze Quant Packet.
6. Run GPT-FEATURE and freeze Feature Packet.
7. Build fresh independent strength/squad/context layers using anti-double-counting groups.
8. Run the normal qualitative full SOP **without using Betfair Shadow as decision evidence**.
9. Freeze Baseline H1 / Baseline grade / Baseline ticket state.
10. Run the normal independent H2 Red Team and freeze the formal Baseline adjudication.
11. **Auto-acquire OddsPapi Betfair Exchange for the selected test match:** if no valid current Exchange Packet exists, resolve the Titan match into `config/exchange_watchlist.json` using match_id, English team aliases and kickoff UTC, then trigger the repository Exchange collector via the watchlist push. The user must not be asked to edit the watchlist manually. If collection fails, disclose it and mark Exchange MISSING; never fabricate it.
12. If a real pre-match Betfair Exchange packet/historical stream is available, map the exact market and run GPT-EXCHANGE.
13. Run `gpt/exchange_shadow_rules.py` against `config/exchange_rulebook.json` and emit every shadow rule as TRIGGERED / NOT_TRIGGERED / MISSING / UNRESOLVED / CONFLICT.
14. Build the separate Exchange-Enhanced shadow view and classify incremental effect versus frozen Baseline: CORRECTED / LED_WRONG / REINFORCED_WRONG / REINFORCED_RIGHT / NO_EFFECT / INSUFFICIENT_DATA.
15. Present formal Baseline and Exchange Shadow separately; never merge their statistics during the test period.

## Exchange auto-acquisition rules
- Primary provider: OddsPapi v4; Betfair Exchange bookmaker `betfair-ex`; football sportId=10; Full Time Result market 101.
- Only selected deep/full-SOP test matches are auto-added to the watchlist. Do not scan every fixture.
- Preserve provider timestamps and `exchangeMeta` raw before interpretation.
- Current Exchange collection is quota-controlled. Do not waste requests on matches not selected for deep analysis.
- A Titan bookmaker row named Betfair is not a substitute for OddsPapi `betfair-ex` Exchange data.
- The runtime should automatically clean or disable expired watchlist targets when practical; stale targets must never create in-play contamination.

## Shadow rulebook source fidelity
- Canonical rules: `config/exchange_rulebook.json`.
- Section 3.2 source header says 10 rules, but merged screenshots visibly contain 11: R61, R62, R63, R64, R65, R66, R67, R74, R75, R76, R77. Preserve all visible rules and keep the source-count conflict as QC.
- R61 uses the word “接近” without a numeric tolerance; automatic trigger is UNRESOLVED until a threshold exists.
- R96 and R99 refer to three validation conditions that are not visible in supplied screenshots; both stay UNRESOLVED.
- Terms like 诱盘/控盘/操纵 are heuristic source labels, not factual claims.

## Fast-ticket rule
Near kickoff, send the formal Baseline actionable direction first. Exchange Shadow must never delay the formal ticket. If Exchange collection would delay execution, issue Baseline first and label Shadow pending/missing.

## Missing/stale data
Missing evidence is not negative evidence. Critical stale/conflict/missing states can block the affected module. Never fabricate a number or silently substitute a source; name missing core timelines/current lineup uncertainty. Betfair is conditional and its absence alone never downgrades the formal Baseline.

## Betfair interpretation
Betfair Exchange is a market microstructure source, not a smart-money oracle. Traded volume, order-book imbalance and price motion are descriptive features and must not independently create a formal direction. Cross-venue comparisons require the closest same-time slice and pre-match state.

## External integrations
Public GitHub libraries are method/data adapters, not decision-makers. Transfermarkt-datasets is historical-only while the 2026 update pause remains; soccerdata scrapers require per-run source QC; socceraction/kloppy activate only with suitable event data; betfairlightweight/betfairutil/flumine activate only with real Betfair data.

## Version discipline
Every full analysis internally records model, Quant Engine, Feature Engine, Exchange Engine and Shadow Rule Engine versions when used. Any formula/threshold/module-status change requires version/changelog update and walk-forward validation. Never rewrite historical calculations with newer formulas.
