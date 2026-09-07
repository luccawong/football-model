# GPT Runtime Contract — Full Stack 1.1

This repository is the persistent cross-chat source of truth for the GPT football analysis stack, not a standalone web application.

## Full-SOP trigger
When the user supplies football match data and requests the full SOP with independent Red Team review, automatically execute the current repository stack without requiring the user to name individual modules.

## Fixed cross-chat order
1. Read MANIFEST, quant/full-stack/exchange configs and module registry.
2. Parse Titan input preserving match ID/state, timestamps, company identity, MAIN/ALT, raw prices and QC.
3. Build module states: ACTIVE/PARTIAL/MISSING/STALE/CONFLICT/RESEARCH_ONLY; never silently omit a registered module.
4. Run snapshot/freshness/identity/same-time/conflict QC.
5. Run GPT-QUANT and freeze Quant Packet.
6. Run GPT-FEATURE and freeze Feature Packet.
7. If a real Betfair Exchange feed or historical stream is supplied/available, map the exact market, run GPT-EXCHANGE and freeze Exchange Packet. If unavailable, mark the exchange modules MISSING and continue without penalty.
8. Build fresh independent strength/squad/context layers using anti-double-counting groups.
9. Run qualitative full SOP including exchange-vs-bookmaker evidence when valid.
10. Freeze H1.
11. Run coherent independent H2 Red Team.
12. Adjudicate CONFIRM/DOWNGRADE/OVERTURN and issue ticket/non-main/PASS under standing rules.

## Fast-ticket rule
Near kickoff, send the actionable direction first, then audit detail. The full stack must not become an excuse to miss kickoff.

## Missing/stale data
Missing evidence is not negative evidence. Critical stale/conflict/missing states can block the affected module. Never fabricate a number or silently substitute a source; name missing core timelines/current lineup uncertainty. Betfair is conditional and its absence alone never downgrades a match.

## Betfair interpretation
Betfair Exchange is a market microstructure source, not a smart-money oracle. Total matched, order-book imbalance and price motion are descriptive features and must not independently create a direction. Cross-venue comparisons require the closest same-time slice and pre-match state.

## External integrations
Public GitHub libraries are method/data adapters, not decision-makers. Transfermarkt-datasets is historical-only while the 2026 update pause remains; soccerdata scrapers require per-run source QC; socceraction/kloppy activate only with suitable event data; betfairlightweight/betfairutil/flumine activate only with real Betfair data.

## Version discipline
Every full analysis internally records model, Quant Engine, Feature Engine and (when used) Exchange Engine versions. Any formula/threshold/module-status change requires version/changelog update and walk-forward validation. Never rewrite historical calculations with newer formulas.
