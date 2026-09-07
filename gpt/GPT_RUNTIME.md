# GPT Runtime Contract — Full Stack

This repository is the persistent cross-chat source of truth for the GPT football analysis stack, not a standalone web application.

## Full-SOP trigger
When the user supplies football match data and requests the full SOP with independent Red Team review, automatically execute the current repository stack without requiring the user to name individual modules.

## Fixed cross-chat order
1. Read MANIFEST, quant/full-stack configs and module registry.
2. Parse Titan input preserving match ID/state, timestamps, company identity, MAIN/ALT, raw prices and QC.
3. Build module states: ACTIVE/PARTIAL/MISSING/STALE/CONFLICT/RESEARCH_ONLY; never silently omit a registered module.
4. Run snapshot/freshness/identity/same-time/conflict QC.
5. Run GPT-QUANT and freeze Quant Packet.
6. Run GPT-FEATURE and freeze Feature Packet.
7. Build fresh independent strength/squad/context layers using anti-double-counting groups.
8. Run qualitative full SOP.
9. Freeze H1.
10. Run coherent independent H2 Red Team.
11. Adjudicate CONFIRM/DOWNGRADE/OVERTURN and issue ticket/non-main/PASS under standing rules.

## Fast-ticket rule
Near kickoff, send the actionable direction first, then audit detail. The full stack must not become an excuse to miss kickoff.

## Missing/stale data
Missing evidence is not negative evidence. Critical stale/conflict/missing states can block the affected module. Never fabricate a number or silently substitute a source; name missing core timelines/current lineup uncertainty.

## External integrations
Public GitHub libraries are method/data adapters, not decision-makers. Transfermarkt-datasets is historical-only while the 2026 update pause remains; soccerdata scrapers require per-run source QC; socceraction/kloppy activate only with suitable event data.

## Version discipline
Every full analysis internally records model, Quant Engine and Feature Engine versions. Any formula/threshold/module-status change requires version/changelog update and walk-forward validation. Never rewrite historical calculations with newer formulas.
