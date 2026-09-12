# GPT Football Analysis SOP — MODEL_1 Full Stack v1.8

Default model: `MODEL_1` from `config/model_registry.json`.

This is the mandatory full-analysis order. Do not reorder or compress these stages unless the user explicitly changes MODEL_1. Formal MODEL_1 semantics are frozen from 2026-09-10 through 2026-10-10 Beijing time under `config/model_1_freeze.json`.

## Analysis-depth rule

- Deep analysis is match-by-match. One match at a time is preferred; two is the practical maximum before depth-compression risk.
- If more than two matches are supplied, keep each match separate and do not skip/compress required stages merely to finish faster.
- Each match must receive its own H1, Red Team H2 and final formal ticket.
- Near kickoff, ticket-first delivery is allowed, but internal SOP stages are not waived.

## Formal market-source rule

- MODEL_1 formal odds/market analysis is Titan-only.
- Titan is the only formal source for 1X2, AH, OU, line/water lifecycle and company timeline when the user supplies a Titan packet.
- JCB and Sporttery are disabled and must not be used even as auxiliary evidence.
- The GitHub draw-exclusion label remains a separate execution constraint, not an odds source.
- Off-field official/media/weather information remains a separate context layer, not a replacement market source.
- OddsPapi/Betfair remains SHADOW_RESEARCH only and has zero formal ticket impact.

1. **Fundamentals first**
   - review recent matches one by one, not only aggregate W-D-L;
   - record who each win came against and who each loss came against;
   - weight opponent quality conceptually: beating a weak side is not equal to beating a strong side, and losing narrowly to an elite side is not equal to losing to a weak side;
   - inspect how the team won/lost: score margin, match state, home/away context, shots/xG/chance quality where available, repeatability and whether the result was flattering/misleading;
   - include recent head-to-head with recency/context only, never as a standalone causal rule;
   - include future 7–10 day schedule and priority pressure, not only past rest;
   - audit rotation, travel, expected core minutes, squad depth and whether a favourite can economically win without covering a deep line;
   - do not invent arbitrary numeric weights before historical calibration.
2. **Market snapshot + Data Gate**
   - state, timestamp, identity, MAIN/ALT, freshness, conflicts and missing core timelines;
   - explicitly name any key missing company/module and state whether the absence affects direction, grade or only confidence in one sub-module;
   - opening/current values are not a substitute for a real time axis; missing timeline nodes remain MISSING and are not interpolated.
3. **Opening-only first impression**: judge the opening structure without later injuries, lineups, schedule, weather or movement contaminating the first impression.
4. **Opening rationality / lifecycle**
   - establish a reasonable opening band from fundamentals before interpreting the quote;
   - true opening vs information re-opening vs ordinary movement;
   - assess whether an old opening remains valid after intervening matches/news;
   - check adjacent counterfactual prices/lines: why this opening rather than the neighboring alternative;
   - blocking/inducement/attraction/market-intent explanations are inference, not verified fact;
   - an unusually high/low favourite quote does not by itself delete the draw path.
5. **Off-field impact / weather — mandatory visible section**
   - use `config/off_field_weather_policy.json`;
   - output weather in every full analysis. If reliable data cannot be verified, output `WEATHER_DATA_MISSING` rather than silently omitting it;
   - information hierarchy: latest official club/league/competition/confirmed-lineup information > same-day reputable mainstream/beat reporting > same-day off-field digest > older context > unverified rumour/hypothesis;
   - current/near-kickoff environment: precipitation intensity and thunderstorm risk, wind/gusts, temperature, humidity/heat stress/WBGT when available, venue altitude, pitch/drainage/standing-water/roof status;
   - travel/circadian: long-haul or transmeridian travel, time-zone direction, arrival time, sleep/recovery opportunity and body-clock mismatch when relevant;
   - two-leg ties: use aggregate score, qualification incentives, rules, venue and opponent style. Do not mechanically map first-leg lead/trail into a betting direction;
   - psychology: manager change, morale rebound, complacency, emotional letdown and end-season motivation require identifiable evidence plus a plausible mechanism; guard against regression-to-the-mean and post-hoc storytelling;
   - national-team chemistry: review continuity, shared-club/cohort familiarity, training time, coach tenure and lineup turnover; do not use fixed player-count bonuses/penalties;
   - relationship/reciprocity: review ownership/multi-club groups, management/coaching/agent networks, loans/transfers, academy/satellite relations, local business/political ties, historic friendly/hostile ties and table incentives; verified facts and reciprocity hypotheses must remain separate;
   - host-face/bilateral/ceremonial narratives may be logged only with concrete public evidence; otherwise they remain unverified and carry no formal weight;
   - weather is a path modifier, not a predetermined Over/Under rule. Heavy rain may suppress technical execution but can also increase slips, goalkeeper handling errors, set-piece volatility and transition mistakes;
   - home geography/climate familiarity is residual context only and must not be double-counted on top of the existing HFA baseline;
   - reject uncalibrated fixed shortcuts: no universal heat/humidity x-goal debuff, altitude second-half x0.7, rain -0.5/-1/-1.5 goals, kickoff-time -0.2/-0.3/-0.5, new-manager +1, complacency -0.5, end-season -1, same-club-count +0.5, club-bond +1/+0.5/+0.3, or rest>=6 days attack -0.2;
   - opaque V1/V2/V3/V4 tactical-counter weights belong nowhere in Stage 5 and are not part of MODEL_1 without definition/validation.
6. **Lineup / tactics**: official vs predicted XI distinction, injuries/suspensions, expected-minutes relevance, formation, tactical matchup, set pieces/pressing/goalkeeper when adequate data exist.
7. **1X2 pricing + Real-Open / Camouflage-Open Audit（实开 / 韬开）**
   - this audit occurs only after fundamentals are established;
   - use the fundamentals baseline to judge whether the opening/1X2 structure is broadly pricing the real strength gap or contains a camouflage/hidden-pricing structure;
   - real-open/camouflage-open is a prior/diagnostic classification, never a mechanical result rule;
   - WH/Lad primary pair; Interwetten cold-side; Pinnacle capital anchor, not automatic smart money; Macau Asian signal; Bet365 comparator; HKJC Asian/local comparator;
   - use de-vigged closest same-time slices from Titan; preserve real European odds separately from probabilities;
   - compare structural opening divergence and later divergence expansion;
   - split favourite win from favourite non-win, then split non-win into draw-led vs underdog-win-led paths.
8. **Asian handicap + European-to-Asian Conversion Audit（欧亚转换）**
   - run only after the 1X2 conclusion is formed;
   - use Titan AH line/water lifecycle;
   - test whether 1X2 strength, draw structure and AH line/water translate coherently;
   - inspect failed upgrades, reversals, adjacent counterfactual lines and company-specific conflicts;
   - any 1X2-AH inconsistency must be explained, not averaged away;
   - favourite win probability is not the same as deep-handicap cover probability;
   - do not upgrade beyond the observed market ceiling without stable deeper-line consensus.
9. **Independent totals / OU**
   - Titan Macau/Pinnacle/Bet365 dynamic structure + OU ladder latent mean;
   - Titan WH/Lad Base-2.5 probability anchor only;
   - totals must be determined independently from AH;
   - JCB/Sporttery are disabled and must not enter the OU conclusion.
10. **Cross-market coherence**: connect Titan 1X2, AH and OU as linked prices; test whether the implied match paths agree or conflict.
11. **Market attraction**
   - assess favourite heat and weak-side betting story/public attraction;
   - use attraction as context for interpreting protection/rejection, never as standalone proof.
12. **External Draw-Exclusion Website + Winner Audit**
   - query `draw_exclusion/index.json` separately at `by_market.JC.by_titan_match_id` and `by_market.BD.by_titan_match_id`; fall back to `latest.json` -> referenced daily file, filtering the selected market;
   - JC is PRIMARY_LAYER and BD is SECONDARY_VALIDATION_LAYER. All execution constraints below apply only to JC;
   - JC=1/BD=1: strong exclusion signal; JC=1/BD=0: follow JC and preserve BD counterevidence; JC=0/BD=1: do not exclude, retain BD risk hint; JC=0/BD=0: no exclusion signal;
   - missing JC stays UNKNOWN; BD never substitutes for JC. Preserve both layer labels, statuses, snapshot IDs/times, sources and provenance;
   - during the one-month test beginning 2026-09-09, `EXCLUDED=1` is a hard execution constraint: remove draw immediately and open HOME WIN vs AWAY WIN audit;
   - do not independently veto the website's draw exclusion during the test;
   - `NOT_EXCLUDED=0` is not a draw prediction, but requires enhanced draw audit: WH/Lad draw position, all core-company de-vig draw probabilities, draw lifecycle, same-time divergence, AH/1X2/OU coherence and draw score mass;
   - UNKNOWN/absent remains UNKNOWN;
   - JC and BD teacher/model families remain separated in research and are not pooled by default.
13. **Underdog Outright Audit（下盘独赢）**
   - mandatory for favourite handicap -0.75 and deeper and central in draw-excluded winner-only review;
   - compare Titan WH, Ladbrokes, Bet365, Pinnacle, Interwetten, Macau and HKJC weak-side outright prices after de-vigging;
   - distinguish structural opening divergence from dynamic divergence expansion;
   - compare company residual versus match median and historical normal bias when calibrated;
   - inspect AH deepening with weak-side outright protection, AH retreat with weak-side strengthening, two-ended win-tail strengthening and cross-company independent clusters;
   - never convert +AH support into outright-upset evidence without 1X2 support;
   - U0/U1/U2/U3 describe quality of upset evidence, not absolute underdog probability;
   - Red Team must later ask whether the analysis invented reasons for the favourite while ignoring weak-side outright pricing evidence.
14. **Correct score — repository Poisson / Dixon-Coles / Bayesian framework**
   - use Titan-derived market inputs for the quantitative market layer plus context/Bayesian update;
   - maximum Top3 final scorelines, preserving explicit Top1/Top2/Top3 ranking;
   - enforce direction consistency with final 1X2/AH/OU path;
   - account for 5+ team-goal tail in deep handicap/high-total matches;
   - never reconstruct or re-rank pre-match score candidates after seeing the result;
   - **OU ↔ correct-score recommendation consistency is a hard output gate**: the final recommended OU direction and the recommended scorelines must not contradict each other on total goals;
   - prohibited contradiction A: recommend Over > X.XX while both Top1 and Top2 total goals are at or below the OU threshold;
   - prohibited contradiction B: recommend Under < X.XX while both Top1 and Top2 total goals are at or above the OU threshold;
   - prohibited contradiction C: recommend Over 2.5 while Top1 is 1-0 or 0-0;
   - prohibited contradiction D: recommend Under 2.5 while Top1 is 2-1 or 3-2;
   - after the conclusion quick table and before the core narrative, output an explicit consistency declaration containing: OU direction + line, Top1 + total goals + compliant/non-compliant, Top2 + total goals + compliant/non-compliant;
   - at least one of Top1 or Top2 must fully comply with the recommended OU direction. If neither complies, the output is invalid and the OU or correct-score derivation must be rerun before any final answer is allowed;
   - this gate applies to the **recommendation/output layer**. It does not erase probability mass on the opposite side of the OU line inside the underlying Poisson/Dixon-Coles/Bayesian distribution.
15. **Uncertainty audit**
   - company/model disagreement, OOD/missingness, stale/conflicting sources, unresolved modules and execution sensitivity;
   - generic 'risk exists' is not itself a downgrade reason. Distinguish risk presence from material counterevidence that changes the result path, pricing structure, cover ceiling or execution viability.
16. **Freeze H1**: freeze first-pass direction, grade, line and key evidence before Red Team.
17. **Independent Red Team H2**
   - construct the strongest coherent alternative, not a cosmetic objection;
   - may CONFIRM / DOWNGRADE / UPGRADE / OVERTURN;
   - for NOT_EXCLUDED matches, explicitly test draw as leading favourite-failure path;
   - for deep favourites, explicitly test favourite win-no-cover and underdog outright;
   - explicitly test whether 1X2 win strength has been incorrectly converted into AH cover confidence;
   - do not DOWNGRADE for generic risk alone; a downgrade needs material pricing/path/cross-market/cover-ceiling/data-integrity counterevidence;
   - do not UPGRADE beyond the demonstrated market ceiling without stable deeper consensus.
18. **Final formal main ticket**
   - exactly ONE formal main ticket per fully analysed match;
   - non-main tickets are abolished;
   - final PASS is not allowed under current MODEL_1 policy; uncertainty is expressed by grade and execution conditions;
   - near kickoff, send ticket first: market/line + grade + actionable reference price + one-sentence core logic;
   - once actionable, ticket is LOCKED; any later change requires explicit correction `old -> new`;
   - if the available market moves to a materially different line, re-audit that current line rather than silently transferring the old grade.

## Favourite-failure decomposition

For strong favourites / hot sides, always separate:

1. favourite wins and covers;
2. favourite wins but does not cover;
3. draw;
4. underdog wins outright.

When draw is hard-excluded by the website during the current test, remove path 3 from execution and immediately compare favourite win versus underdog outright win before judging cover depth.

## Price / value interpretation

- Thin theoretical EV/value alone does not invalidate a stable direction.
- Separate payout/EV change from information change.
- Only information/structure change is a core reason to correct direction.
- Long-run execution generally prefers decimal odds around 1.80 or better, while exact minimum remains ticket-specific.

## Canonical loading order

1. `config/model_registry.json`
2. `models/MODEL_1_DEFAULT.md` for MODEL_1
3. `gpt/FOOTBALL_CANONICAL_MEMORY.md`
4. `config/active_decision_policy.json`
5. `config/off_field_weather_policy.json`
6. `gpt/FOOTBALL_SOP.md`
7. `config/module_registry.json`
8. `config/model_1_trace_contract.json`
9. `config/model_1_supporting_contracts.json`
10. `config/model_1_freeze.json`
11. `gpt/MEMORY_GAP_AUDIT_2026-09-09.md` as supporting audit only
12. `config/full_stack_config.json`
13. dedicated Exchange/draw-exclusion research files

## Formal trace / packet audit

- `gpt/decision_engine.py` enforces stage-level policy gates.
- `gpt/formal_trace.py` validates and serializes the 18-stage pre-match trace.
- `gpt/model_1_packet_bridge.py` maps existing Quant/Feature outputs into formal stage evidence without changing validated mathematical formulas.
- Missing packets/timelines/nodes stay explicit MISSING; do not silently substitute or backfill.

## Validation and freeze

Use chronological walk-forward Brier/RPS/log-loss/reliability. Do not change MODEL_1 from a few outcomes. Prefer an adequate prospective block (roughly 30-50 comparable full analyses is a practical first review window unless a hard logic/data bug appears). Prefer league-specific calibration; Chinese football stays separate for research/calibration.

During the formal freeze through 2026-10-10 Beijing time, new ideas are LOG_ONLY for future MODEL_2 consideration. Parser/QC/data-identity bug fixes and tests are allowed only when they restore the frozen semantics rather than change them. This OU-score recommendation consistency gate is an explicit user-authorized MODEL_1 override on 2026-09-11 and therefore is formal immediately.
