# GPT Runtime Contract — MODEL_1 Default / Full Stack 1.5

This repository is the persistent cross-chat source of truth for the GPT football analysis stack.

## Model selection

- Read `config/model_registry.json` first.
- Default model is `MODEL_1` unless the user explicitly selects or creates another model.
- MODEL_1 identity must never be overwritten by a future rebuild. If performance later fails to meet expectations, freeze MODEL_1 and create MODEL_2/3/etc with separate rules, activation date and validation.
- Current MODEL_1 profile: `models/MODEL_1_DEFAULT.md`.

## Full-SOP trigger

When the user supplies football match data and requests full SOP + independent Red Team, automatically execute the current default model without requiring the user to name individual modules.

## Canonical loading order

1. `config/model_registry.json`
2. active model profile, currently `models/MODEL_1_DEFAULT.md`
3. `gpt/FOOTBALL_CANONICAL_MEMORY.md`
4. `config/active_decision_policy.json`
5. `gpt/FOOTBALL_SOP.md`
6. `config/module_registry.json`
7. `config/model_1_trace_contract.json`
8. `config/model_1_supporting_contracts.json`
9. `gpt/MEMORY_GAP_AUDIT_2026-09-09.md` as supporting audit only; ACTIVE items may supplement but research/legacy/conflict items cannot override formal policy
10. `config/full_stack_config.json`
11. dedicated Exchange / draw-exclusion files

## MODEL_1 formal analysis order

The formal trace must follow exactly:

1. Fundamentals
2. Market snapshot
3. Opening first impression
4. Opening rationality / lifecycle
5. Off-field factors / weather
6. Lineup / tactics
7. 1X2 + real-open/camouflage-open（实开/韬开）audit after fundamentals
8. Asian handicap + explicit 1X2 -> AH European/Asian conversion consistency audit
9. Totals / OU
10. Cross-market coherence
11. Market attraction
12. External draw-exclusion website + winner audit
13. Underdog outright audit
14. Correct score using repository Poisson/Dixon-Coles/Bayesian framework
15. Uncertainty audit
16. Freeze H1
17. Independent Red Team H2
18. Exactly one formal main ticket

`gpt/decision_engine.py` validates policy gates. `gpt/formal_trace.py` validates and serializes the complete 18-stage audit trace. Research/shadow modules run outside the frozen formal trace and cannot reorder it.

## Formal runtime packets

Every full MODEL_1 analysis should preserve three linked evidence objects plus the final trace:

- Quant Packet from `gpt/quant_core.py`;
- Feature/QC Packet mapped by `gpt/model_1_packet_bridge.py`;
- correct-score stage evidence mapped from Quant + explicit Bayesian/context update by `gpt/model_1_packet_bridge.py`;
- Formal Analysis Trace from `gpt/formal_trace.py`.

The packet bridge is orchestration only. It must not change validated de-vig, Poisson/Dixon-Coles, AH/OU settlement or uncertainty mathematics merely to fit the SOP.

If an expected packet is unavailable, store explicit `MISSING`; never silently substitute another source or infer a missing time point.

## Fundamentals first

Before looking for a market narrative, evaluate recent matches one by one:

- who each win/loss came against;
- opponent quality;
- how the team won/lost: margin, game state, home/away context, shots/xG/chance quality where available;
- recent head-to-head with context;
- future schedule and priority pressure.

Do not invent arbitrary numeric opponent weights until calibrated.

## 1X2 and AH transition gates

- 1X2 must include the post-fundamentals 实开/韬开 audit. It is a diagnostic/prior, not a mechanical result rule.
- AH runs after 1X2 and must explicitly test 欧亚转换 consistency. Any conflict must be explained.
- Never convert strong favourite 1X2 win confidence directly into deep-AH cover confidence.

## Draw-exclusion hard test

Authoritative source: `draw_exclusion/latest.json` -> referenced daily file.

- `EXCLUDED=1`: hard-remove draw from the execution branch for the current one-month test and immediately run HOME WIN vs AWAY WIN audit. Do not independently veto the website label during the test.
- `NOT_EXCLUDED=0`: keep draw active and run enhanced draw audit; this is not itself a draw prediction.
- missing/UNKNOWN stays UNKNOWN.

Draw research must preserve teacher/model family where available. `JC_DRAW_MODEL` and `BD_DRAW_MODEL` are separate research families and are not pooled by default.

## Underdog outright gate

- Mandatory for favourites -0.75 and deeper.
- Mandatory in winner-only review after hard draw exclusion.
- Must distinguish +AH cover evidence from outright-win evidence.
- Historical company-residual / divergence thresholds remain research-only until calibrated under `research/underdog_outright/RESEARCH_PROTOCOL.md`.

## Formal ticket policy

- Exactly one formal main ticket per full analysis.
- No non-main tickets.
- No final PASS in MODEL_1; uncertainty is expressed through grade and execution conditions.
- Near kickoff send the formal main first.
- Once actionable, the ticket is locked; any later change must be explicit `old -> new` correction.

## Analysis-depth rule

Deep analysis is match-by-match. One match at a time is preferred; two is the practical maximum before depth compression risk. If more are supplied, do not skip/reorder required stages merely to finish faster.

## Current Betfair mode

Betfair/OddsPapi is **SHADOW_RESEARCH** with zero formal impact.

Hard separation:

- Freeze the complete formal MODEL_1 Baseline before Exchange Shadow interpretation.
- Exchange Shadow does not alter formal ticket direction/grade and is excluded from formal statistics.
- If collection fails, disclose MISSING; never fabricate.
- A Titan bookmaker row named Betfair is not OddsPapi `betfair-ex` Exchange data.

## Exchange auto-acquisition

- Primary provider: OddsPapi v4; `betfair-ex`; football sportId=10; Full Time Result market 101.
- Only selected deep/full-SOP research matches are auto-added to watchlist.
- Preserve provider timestamps and raw exchangeMeta.
- Exchange collection must never delay the formal ticket near kickoff.

## Prospective validation support

Use `validation/MODEL_1_FORWARD_VALIDATION.md` for measurement discipline around MODEL_1. Where the collector supports it, retain T-5h/T-2h/T-1h/T-30m/T-10m checkpoints, candidate provenance, result-confirmation status and objective quarter-line settlement. These validation controls do not become betting signals.

## Missing/stale data

Missing evidence is not negative evidence. Critical stale/conflict/missing states can block the affected calculation but must be disclosed. Never fabricate company timelines, lineup identity, or market fields. Missing sampling nodes are not interpolated from Opening/Current.

## Version discipline

Every full analysis should record model ID/version, policy version, Quant Engine, Feature Engine, packet-bridge version, trace-engine version and any Shadow engine version used. Formula/threshold/module-status changes require changelog + prospective validation. Historical MODEL_1 outputs are never rewritten by newer models.
