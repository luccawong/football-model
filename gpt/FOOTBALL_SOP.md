# GPT Football Analysis SOP — MODEL_1 Full Stack v1.6

Default model: `MODEL_1` from `config/model_registry.json`.

This is the mandatory full-analysis order. Do not reorder or compress these stages unless the user explicitly changes MODEL_1.

## Analysis-depth rule

- Deep analysis is match-by-match. One match at a time is preferred; two is the practical maximum before depth-compression risk.
- If more than two matches are supplied, keep each match separate and do not skip/compress required stages merely to finish faster.
- Each match must receive its own H1, Red Team H2 and final formal ticket.
- Near kickoff, ticket-first delivery is allowed, but internal SOP stages are not waived.

## Formal market-source rule

- MODEL_1 formal odds/market analysis is **Titan-only**.
- Titan is the only formal source for 1X2, AH, OU, line/water lifecycle and company timeline when the user supplies a Titan packet.
- JCB and Sporttery are currently **disabled** and must not be used even as auxiliary evidence.
- The GitHub draw-exclusion label remains a separate execution constraint, not an odds source.
- Off-field official/media/weather information remains a separate context layer, not a replacement market source.
- OddsPapi/Betfair remains SHADOW_RESEARCH only and has zero formal ticket impact.

1. **Fundamentals first**
   - review recent matches one by one, not only aggregate W-D-L;
   - record who each win came against and who each loss came against;
   - weight opponent quality conceptually: beating a weak side is not equal to beating a strong side, and losing narrowly to an elite side is not equal to losing to a weak side;
   - inspect how the team won/lost: score margin, match state, home/away context, shots/xG/chance quality where available, repeatability and whether the result was flattering/misleading;
   - include recent head-to-head with recency/context only, never as a standalone causal rule;
   - include future schedule and priority pressure, not only past rest;
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
5. **Off-field impact / weather**: official club/league information first, then major media/beat reporting; include motivation, relationship/reciprocity, travel, weather/pitch/referee when relevant; label rumours.
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
   - authoritative source: `draw_exclusion/latest.json` -> referenced daily file;
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
   - never reconstruct or re-rank pre-match score candidates after seeing the result.
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
   - if the available market moves to a materially different line, re-audit that current line rather than silently transferring the old grade; legacy 'price below threshold = PASS' rules are superseded by the current exactly-one-main policy.

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
5. `gpt/FOOTBALL_SOP.md`
6. `config/module_registry.json`
7. `config/model_1_trace_contract.json`
8. `config/model_1_supporting_contracts.json`
9. `gpt/MEMORY_GAP_AUDIT_2026-09-09.md` as supporting audit only
10. `config/full_stack_config.json`
11. dedicated Exchange/draw-exclusion research files

## Formal trace / packet audit

- `gpt/decision_engine.py` enforces stage-level policy gates.
- `gpt/formal_trace.py` validates and serializes the 18-stage pre-match trace.
- `gpt/model_1_packet_bridge.py` maps existing Quant/Feature outputs into formal stage evidence without changing validated mathematical formulas.
- Missing packets/timelines/nodes stay explicit MISSING; do not silently substitute or backfill.

## Divergence validation protocol

The Defensive Divergence Stack remains `RESEARCH_ONLY_UNCALIBRATED` until prospective validation is adequate. Store the full pre-match snapshot first, then settle outcomes later. Validate by league/market/handicap bucket: target-side divergence magnitude, attraction, persistence, independent clusters, lead-lag, cross-market confirmation and actual path split. Do not select thresholds after results.

## Validation

Use chronological walk-forward Brier/RPS/log-loss/reliability. Do not change MODEL_1 from a few outcomes. Prefer an adequate prospective block (roughly 30-50 comparable full analyses is a practical first review window unless a hard logic/data bug appears). Prefer league-specific calibration; Chinese football stays separate for research/calibration. Black-box ML, Kelly and live-inplay Bayesian remain RESEARCH_ONLY until promoted after validation.
