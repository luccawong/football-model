# GPT Runtime Contract — Full Stack 1.2

This repository is the persistent cross-chat source of truth for the GPT football analysis stack, not a standalone web application.

## Full-SOP trigger
When the user supplies football match data and requests the full SOP with independent Red Team review, automatically execute the current repository stack without requiring the user to name individual modules.

## Fixed cross-chat order
1. Read MANIFEST, quant/full-stack/exchange configs and module registry.
2. Parse Titan input preserving match ID/state, timestamps, company identity, MAIN/ALT, raw prices and QC.
3. Build module states: ACTIVE/PARTIAL/MISSING/STALE/CONFLICT/RESEARCH_ONLY; never silently omit a registered module.
4. Run snapshot/freshness/identity/same-time/conflict QC.
5. **Auto-acquire OddsPapi Betfair Exchange for the selected full-SOP match:** if no valid current Exchange Packet exists, resolve the Titan match into `config/exchange_watchlist.json` using match_id, English team aliases and kickoff UTC, then trigger the repository Exchange collector via the watchlist push. The user must not be asked to edit the watchlist manually. Use the resulting packet in the same analysis turn when available. If collection fails or does not produce a valid pre-match packet, disclose the failure and mark Exchange MISSING; never fabricate it.
6. Run GPT-QUANT and freeze Quant Packet.
7. Run GPT-FEATURE and freeze Feature Packet.
8. If a real Betfair Exchange feed/current packet/historical stream is available, map the exact market, run GPT-EXCHANGE and freeze Exchange Packet. If unavailable, mark the exchange modules MISSING and continue without penalty.
9. Build fresh independent strength/squad/context layers using anti-double-counting groups.
10. Run qualitative full SOP including exchange-vs-bookmaker evidence when valid.
11. Freeze H1.
12. Run coherent independent H2 Red Team.
13. Adjudicate CONFIRM/DOWNGRADE/OVERTURN and issue ticket/non-main/PASS under standing rules.

## Exchange auto-acquisition rules
- Primary provider: OddsPapi v4; Betfair Exchange bookmaker `betfair-ex`; football sportId=10; Full Time Result market 101.
- Only selected deep/full-SOP matches are auto-added to the watchlist. Do not scan every fixture.
- Preserve provider timestamps and `exchangeMeta` raw before interpretation.
- Current Exchange collection is quota-controlled. Do not waste requests on matches not selected for deep analysis.
- A Titan bookmaker row named Betfair is not a substitute for OddsPapi `betfair-ex` Exchange data.
- The runtime should automatically clean or disable expired watchlist targets when practical; stale targets must never create in-play contamination.

## Fast-ticket rule
Near kickoff, send the actionable direction first, then audit detail. The full stack must not become an excuse to miss kickoff. If Exchange collection would delay a near-kickoff ticket, issue the ticket from validated non-Exchange evidence and label Exchange pending/missing rather than delaying execution.

## Missing/stale data
Missing evidence is not negative evidence. Critical stale/conflict/missing states can block the affected module. Never fabricate a number or silently substitute a source; name missing core timelines/current lineup uncertainty. Betfair is conditional and its absence alone never downgrades a match.

## Betfair interpretation
Betfair Exchange is a market microstructure source, not a smart-money oracle. Total matched, order-book imbalance and price motion are descriptive features and must not independently create a direction. Cross-venue comparisons require the closest same-time slice and pre-match state.

## External integrations
Public GitHub libraries are method/data adapters, not decision-makers. Transfermarkt-datasets is historical-only while the 2026 update pause remains; soccerdata scrapers require per-run source QC; socceraction/kloppy activate only with suitable event data; betfairlightweight/betfairutil/flumine activate only with real Betfair data.

## Version discipline
Every full analysis internally records model, Quant Engine, Feature Engine and (when used) Exchange Engine versions. Any formula/threshold/module-status change requires version/changelog update and walk-forward validation. Never rewrite historical calculations with newer formulas.
