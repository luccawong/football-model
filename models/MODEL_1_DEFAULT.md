# MODEL_1 — Current Default Football Model

Status: ACTIVE_DEFAULT_FROZEN_FORMAL_SEMANTICS
Effective date: 2026-09-09
Formal freeze window: 2026-09-10 through 2026-10-10 (Asia/Shanghai)

This is the first formally registered football model in this repository. It is the default model for full pre-match analysis unless the user explicitly selects or creates another model.

## Purpose

MODEL_1 freezes the current football-analysis philosophy and execution rules so future model rebuilds can be compared against a stable historical baseline rather than silently rewriting the same model.

If MODEL_1 performance later fails to meet the user's expectations, do NOT overwrite its identity or retroactively change its historical outputs. Freeze MODEL_1 and create MODEL_2 with its own rules, activation date, records and validation.

## Canonical files

- `gpt/FOOTBALL_CANONICAL_MEMORY.md`
- `gpt/FOOTBALL_SOP.md`
- `config/active_decision_policy.json`
- `config/model_1_source_policy.json`
- `config/opening_baseline_policy.json`
- `config/off_field_weather_policy.json`
- `config/model_1_freeze.json`
- `config/module_registry.json`
- `config/model_1_trace_contract.json`
- `gpt/decision_engine.py`
- `gpt/formal_trace.py`
- `gpt/model_1_packet_bridge.py`

Supporting audit/validation documents:

- `gpt/MEMORY_GAP_AUDIT_2026-09-09.md`
- `docs/MODEL_1_OFFFIELD_WEATHER_HEURISTIC_AUDIT_20260910.md`
- `validation/MODEL_1_FORWARD_VALIDATION.md`
- `research/underdog_outright/RESEARCH_PROTOCOL.md`
- `draw_exclusion_research/MODEL_FAMILY_PROTOCOL.md`
- `research/pending_model_2/README.md`

Supporting research cannot override formal MODEL_1 policy unless explicitly promoted by a new versioned user instruction.

## Formal market-source policy

- MODEL_1 formal market/odds source is Titan only.
- Titan supplies formal 1X2, AH, OU, line/water lifecycle and bookmaker timeline inputs.
- JCB and Sporttery are disabled: no formal use and no auxiliary use.
- Any historical JCB/Sporttery research file is archive-only and is not loaded by MODEL_1.
- GitHub draw-exclusion labels remain a separate execution constraint, not an odds source.
- Official/media/weather information remains context, not a replacement odds source.
- OddsPapi/Betfair remains SHADOW_RESEARCH with zero formal ticket impact.

## MODEL_1 fixed full-analysis order

1. Fundamentals
2. Market snapshot
3. Opening first impression
4. Opening rationality / lifecycle
5. Off-field factors / weather
6. Lineup / tactics
7. 1X2, including real-open vs camouflage-open audit after fundamentals
8. Asian handicap, including 1X2 -> AH European/Asian conversion consistency
9. Totals / OU
10. Cross-market coherence
11. Market attraction
12. External draw-exclusion website; EXCLUDED immediately opens winner-only audit, NOT_EXCLUDED triggers enhanced draw audit
13. Underdog outright audit
14. Correct score using repository Poisson / Dixon-Coles / Bayesian framework
15. Uncertainty audit
16. Freeze H1
17. Independent Red Team H2
18. Exactly one formal main ticket

## Fundamental layer requirements

Fundamentals are evaluated before market interpretation and must include, when data are available:

- recent match-by-match results, not just aggregate W-D-L;
- who each win came against and who each loss came against;
- opponent-quality weighting rather than treating all wins/losses equally;
- how the team won or lost: margin, game state, shot/xG/chance quality where available, home/away context and whether the result was repeatable;
- recent head-to-head only with context and recency, not as a standalone causal rule;
- future schedule and priority pressure;
- strength of opponents in the upcoming schedule;
- rotation/travel/expected core minutes and whether a favourite can economically win without covering a deep line;
- avoid arbitrary numerical weights until historically calibrated.

## Opening baseline / HFA anti-double-counting

- Build the reasonable opening reference with league-specific historical opening calibration where available.
- Use league HFA baseline plus team-specific home/away residuals; do not stack a full generic home advantage and a second generic away penalty.
- Old rough conversions such as 'about 10 rating points = 1 goal' are seed concepts only, not fixed MODEL_1 constants.
- If league calibration is missing, mark the fair-opening band uncalibrated and widen uncertainty instead of fabricating a precise fair line.

## Stage 5 — Off-field factors / weather

Every full analysis must visibly output the weather subsection. If reliable weather data cannot be obtained, output `WEATHER_DATA_MISSING` rather than omitting weather.

Mandatory environment review when relevant:

- current conditions and near-kickoff forecast/nowcast;
- precipitation intensity, thunderstorm risk, wind and gusts;
- temperature, humidity and heat stress/WBGT when available;
- venue altitude and visitor acclimatization;
- pitch surface, drainage, standing-water risk and roof status;
- long-haul/transmeridian travel, time zones, arrival time, sleep/body-clock mismatch.

Mandatory human/context review when relevant:

- aggregate score/game state in two-leg ties;
- manager change, morale, rebound/letdown and complacency only as evidence-conditioned hypotheses;
- national-team continuity, shared-club/cohort familiarity, training time, coach tenure and lineup turnover;
- ownership/multi-club groups, management/coaching/agent networks, loans/transfers, academy/satellite relations, local business/political ties and table-incentive reciprocity;
- host-face/bilateral/ceremonial narratives only when supported by public evidence; otherwise hypothesis only;
- same-day off-field digest is checked when available, but latest official information overrides earlier reporting.

No universal numeric debuffs/bonuses are accepted for these factors. In particular, MODEL_1 rejects automatic formulas such as heat/humidity x-goal reductions, altitude second-half x0.7, rain -0.5/-1/-1.5 goals, fixed kickoff-time penalties, new-manager +1, complacency -0.5, end-season -1, same-club-player-count bonuses, club-bond +1/+0.5/+0.3, or rest >=6 days attack -0.2.

Weather is a path modifier, not a predetermined Over/Under rule: heavy rain can suppress technical execution but can also raise slips, goalkeeper errors, set-piece volatility and transition mistakes. Home geography/climate familiarity is residual context only and must not be double-counted on top of the existing home-field baseline.

Tactical style-counter rules belong in Stage 6, not Stage 5. Opaque V1/V2/V3/V4 fixed counter weights are not part of MODEL_1.

## Market interpretation constraints

- Opening-only first impression remains uncontaminated by later information.
- Opening rationality must compare the quote with a reasonable fundamental opening band and adjacent counterfactual prices/lines.
- Real-open / camouflage-open classification is a prior/diagnostic layer, not a mechanical result rule.
- 1X2 must use de-vigged same-time company comparison from Titan.
- After 1X2, AH must explicitly test whether European and Asian market translation is coherent or conflicting.
- Favourite win probability must not be confused with deep-handicap cover probability.
- Price/value and result direction are separate; thin EV alone does not invalidate a stable direction.

## Draw-exclusion test

During the one-month forward test beginning 2026-09-09:

- `EXCLUDED=1` is a hard execution constraint: remove draw from the execution branch and immediately audit HOME WIN vs AWAY WIN.
- `NOT_EXCLUDED=0` is not a draw prediction, but draw receives enhanced mandatory audit.
- missing/unknown stays UNKNOWN.
- JC and BD draw-model families are stored separately for research; family research does not override the verified daily execution label.

## Underdog outright audit

- Mandatory for favourites -0.75 and deeper.
- Also central to winner-only review after draw exclusion.
- Compare Titan WH, Ladbrokes, Bet365, Pinnacle, Interwetten, Macau and HKJC.
- Separate underdog AH cover evidence from outright-win evidence.
- U0/U1/U2/U3 grades describe upset-evidence quality, not absolute probability.
- Historical residual/divergence thresholds remain research-only until validated.

## Ticket policy

- Exactly one formal main ticket per fully analysed match.
- No non-main tickets.
- No final PASS under the current MODEL_1 policy; uncertainty is expressed by grade and execution conditions.
- Once an actionable ticket is issued it is locked; any change must be an explicit correction with old -> new.

## Runtime auditability

Every full MODEL_1 analysis should preserve a machine-auditable 18-stage formal trace. Quant/Feature outputs are mapped into the trace through the packet bridge without changing the mathematical engines merely to fit the SOP.

Missing evidence stays MISSING. Missing validation sampling nodes are never interpolated from Opening/Current.

## Validation discipline

- Prefer an adequate prospective block before rebuilding the model; roughly 30-50 comparable full analyses is a practical first review window unless a hard logic/data bug is found.
- Preserve candidate provenance and pre-match freeze.
- Where the collector supports it, preserve T-5h / T-2h / T-1h / T-30m / T-10m snapshots without backfilling missing nodes.
- Confirm real terminal match status before settlement.
- Keep formal model correctness separate from whether the user personally placed the bet.

## One-month formal freeze

From 2026-09-10 through 2026-10-10 Beijing time, do not alter MODEL_1 formal semantics, stage order, source authority, thresholds, ticket policy or module authority based on recent results or new ideas.

Allowed during the freeze: data collection, result/stat updates, parser/QC/identity bug fixes, tests that enforce already-frozen behavior, and logging research ideas for a future MODEL_2 with zero formal impact.

Only an explicit user instruction may end or override this freeze early.

## Research-only layers

- Betfair/OddsPapi Exchange: SHADOW_RESEARCH, zero formal impact.
- Macau post-2026-09-01 regime hypothesis: RESEARCH_ONLY.
- Uncalibrated divergence thresholds remain research until walk-forward validation supports promotion.
- Historical JCB/Sporttery research is archived disabled and not loaded by current MODEL_1.
