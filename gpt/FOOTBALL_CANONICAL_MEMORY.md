# Football Canonical Memory — MODEL_1 Frozen Active Rules

Snapshot date: 2026-09-16 Beijing time
Default model: `MODEL_1`
Registry: `config/model_registry.json`
Freeze contract: `config/model_1_freeze.json`
Active override manifest: `config/model_1_active_overrides_20260914.json`
Current cross-agent handoff: `gpt/MODEL_1_AGENT_HANDOFF_20260916.md`

Purpose: keep the user's active cross-chat football rules in one auditable GitHub source so future analysis does not depend on conversational recall. MODEL_1 is the first/default formal model. If future win rate is unsatisfactory, preserve MODEL_1 and create MODEL_2/3/etc; never silently overwrite MODEL_1 history.

## 1. Authority / versioning

- GitHub `luccawong/football-model` is the canonical rule source.
- Chat memory is auxiliary; a new explicit user instruction takes precedence until GitHub is updated.
- Targeted user-authorized overrides in `config/model_1_active_overrides_20260914.json` supersede conflicting frozen-baseline wording without rewriting historical decisions.
- Rule changes apply prospectively. Do not rewrite old pre-match decisions after results.
- Once an actionable formal ticket is issued, it is LOCKED. Later change must be an explicit correction `old -> new`.
- Separate fact / inference / assumption / conclusion and actively challenge both user and model hypotheses.
- From 2026-09-10 through 2026-10-10 Beijing time, MODEL_1 formal semantics are frozen except for explicit user-authorized targeted overrides.
- As of 2026-09-16, the mandatory independent H2/counter-ticket process is cancelled. Stage 17 is now a **single-H1 falsification audit** under `config/model_1_single_h1_falsification_policy.json`.

## 2. MODEL_1 ticket policy — ACTIVE

- Every fully analysed match produces exactly ONE formal main ticket.
- No non-main tickets.
- No final PASS in MODEL_1; uncertainty is expressed through grade and execution conditions.
- Near kickoff: ticket first = market/line + grade + actionable reference price + one-line logic; explanation follows.
- Formal ticket correctness is the primary model performance metric; user's personal bet/no-bet is separate.

## 3. MODEL_1 mandatory full-analysis order — ACTIVE

1. Fundamentals
2. Market snapshot
3. Opening first impression
4. Opening rationality / lifecycle
5. Off-field factors / weather
6. Lineup / tactics
7. 1X2, including post-fundamentals 实开 / 韬开 audit
8. Asian handicap, including explicit 欧亚转换 consistency after 1X2
9. Totals / OU
10. Cross-market coherence
11. Market attraction
12. External draw-exclusion website; if draw is excluded, immediately open HOME-vs-AWAY winner audit; if not excluded, run enhanced draw audit
13. Underdog outright audit（下盘独赢）
14. Correct score using repository Poisson / Dixon-Coles / Bayesian theory
15. Uncertainty audit / neutral evidence ledger
16. Freeze H1
17. Single-H1 falsification audit
18. Formal main ticket

Quick scan is only match selection and never substitutes for this deep-analysis sequence.

### Stage 17 — ACTIVE 2026-09-16 override

- Do not construct a mandatory H2, second candidate or counter-ticket.
- Keep one working H1.
- After H1 is frozen, aggressively try to falsify it using the strongest counterevidence, explicit failure conditions, alternative match paths and opposite interpretations of the market lifecycle.
- If H1 survives, retain it with any justified grade change.
- If H1 fails, discard it and rebuild H1 directly from the stage 1–15 evidence; then re-run the falsification audit before ticketing.
- Valid outcomes: `SURVIVES`, `DOWNGRADE`, `UPGRADE`, `OVERTURN_AND_REBUILD`.
- Falsification is not a second prediction.

## 4. Formal market source — ACTIVE

- MODEL_1 formal 1X2/AH/OU/line-water/timeline source is Titan only.
- JCB and Sporttery are disabled: no formal use and no auxiliary use.
- Historical JCB/Sporttery research remains archive-only and is not loaded into MODEL_1.
- GitHub draw-exclusion label is a separate execution constraint, not an odds source.
- Official/media/weather data are context sources, not replacement market sources.
- OddsPapi/Betfair remains SHADOW_RESEARCH with zero formal ticket impact.

## 5. Fundamentals first — ACTIVE

Before market interpretation, review:

- recent matches one by one, not only aggregate W-D-L;
- who each win came against and who each loss came against;
- opponent quality: a win over a weak side is not equal to a win over a strong side; a narrow loss to an elite side is not equal to a loss to a weak side;
- how each result happened: margin, game state, home/away context, shots/xG/chance quality where available, whether the result was repeatable or flattering;
- recent head-to-head only with recency/context, not as a standalone causal rule;
- future 7–10 day schedule and priority pressure, including strength/importance of upcoming opponents;
- rotation, travel, expected core minutes, squad depth and whether a favourite can economically win without covering a deep line.

Do not invent arbitrary numerical opponent-quality weights before calibration.

## 6. Opening interpretation / lifecycle — ACTIVE

- Opening first impression uses opening structure only. Later injuries, lineups, schedule, weather, motivation and movement must not contaminate it.
- Then distinguish true opening, information re-opening, and ordinary movement.
- If a quote was posted days earlier and the team played another match afterwards, reassess whether that opening is still a valid anchor.
- Companies whose first quotes are separated materially in time cannot be compared directly; align to the closest common time slice.
- Establish a reasonable opening band from fundamentals and test the adjacent counterfactual: why this price/line rather than the neighbouring alternative.
- Blocking/inducement/market-intent language is inference, never fact without evidence.
- A late synchronized buyback, failed deeper upgrade or synchronized retreat must reopen the lifecycle thesis; do not merely explain it away to protect H1.

## 7. Stage 5 off-field / weather — ACTIVE

Every full analysis must visibly output weather. If reliable weather data are unavailable, output `WEATHER_DATA_MISSING` rather than skipping the section.

Evidence hierarchy:

1. latest official club/league/competition/confirmed-lineup information;
2. same-day reputable mainstream/beat reporting;
3. same-day off-field digest;
4. older context;
5. unverified rumour/hypothesis.

Weather/environment checks when relevant:

- current conditions and near-kickoff forecast/nowcast;
- rain intensity/thunderstorm risk, wind and gusts;
- temperature, humidity and heat stress/WBGT when available;
- venue altitude plus visitor acclimatization and arrival timing;
- pitch surface, drainage, standing water and roof status;
- long-haul/transmeridian travel, time-zone direction, arrival time, sleep and body-clock mismatch.

Human/context checks when relevant:

- two-leg aggregate score, qualification state and competition rules;
- manager change, morale rebound/letdown and complacency only as evidence-conditioned hypotheses;
- national-team continuity, shared-club/cohort familiarity, training time, coach tenure and lineup turnover;
- ownership/multi-club groups, management/coaching/agent networks, loans/transfers, academy/satellite relations, local business/political ties, historic friendly/hostile links and table-incentive reciprocity;
- national-team host-face/bilateral/ceremonial narratives only when there is concrete public evidence; otherwise hypothesis only.

No universal fixed numeric debuffs/bonuses are part of MODEL_1. Reject automatic rules such as heat/humidity x-goal debuffs, altitude second-half x0.7, rain -0.5/-1/-1.5 goals, fixed kickoff-time penalties, new-manager +1, complacency -0.5, end-season -1, same-club-player-count bonuses, club-bond +1/+0.5/+0.3, or rest >=6 days attack -0.2.

Weather modifies match paths, not a predetermined Over/Under direction. Heavy rain may suppress passing/tempo but can also increase slips, goalkeeper handling errors, set-piece volatility and transition mistakes. Home geography/climate familiarity is residual context only and must not be double-counted over the existing HFA baseline.

Tactical style-counter concepts belong in Stage 6. Opaque V1/V2/V3/V4 counter-weight shortcuts are not part of MODEL_1.

### Competition-rules gate

For every cup/knockout match verify, before using game-state incentives:

- single-leg vs two-leg;
- aggregate score if relevant;
- 90-minute market settlement vs advancement;
- extra time vs direct penalties;
- away-goal rules if relevant;
- whether a 90-minute draw is strategically acceptable;
- whether a favourite leading by one needs to chase a second goal.

Never infer `must produce an advancing winner` => `90-minute draw impossible`.

## 8. 1X2 + 实开 / 韬开 — ACTIVE

The real-open/camouflage-open audit runs only after fundamentals are established.

- Use fundamentals to assess whether the market broadly prices the true strength gap (`实开`) or contains a camouflage/hidden-pricing structure (`韬开`).
- This is a prior/diagnostic classification, not a mechanical result rule.
- Historical 实开/韬开 rules and AH×1X2 shortcut rules are priors only; they must not mechanically force a ticket.
- Cross-check classification against company divergence and lifecycle.

Mandatory company roles from Titan:

- William Hill + Ladbrokes = primary pair.
- WH = draw-price location / protection / inducement audit.
- Ladbrokes = home/away win-tail difference.
- Interwetten = cold-side / upset-risk check.
- Pinnacle = capital/market anchor, not automatic smart money.
- Macau = Asian signal and divergence.
- Bet365 = major comparator.
- HKJC = Asian/local comparator when available.

For relevant aligned time slices preserve real European odds, separately compute de-vig H/D/A probabilities, and report company percentage-point differences. Never call de-vig probabilities European odds. Do not conclude `lower favourite price = favourite wins`.

## 9. AH + 欧亚转换 — ACTIVE

- AH runs after 1X2.
- Explicitly test whether 1X2 strength/draw structure converts coherently into the AH line and water.
- Any 1X2-AH conflict must be explained, not averaged away.
- Read line + water lifecycle, failed upgrades, reversals and adjacent counterfactual lines.
- Favourite win probability is not the same as cover probability.
- Do not upgrade beyond the observed market ceiling without stable deeper-line consensus.

For deep favourites separate:
1. favourite wins and covers;
2. favourite wins but does not cover;
3. draw;
4. underdog wins outright.

## 10. Totals / OU — ACTIVE

- OU is a separate core module and must be determined independently from AH.
- Titan Macau/Pinnacle/Bet365 = dynamic mainstream OU.
- Titan WH/Lad fixed 2.5 = Base-2.5 probability anchor, not dynamic line-level comparator.
- Different displayed OU lines require line+price/alternate-ladder normalization to a comparable latent total distribution before calling company disagreement.
- JCB/Sporttery are disabled and cannot enter the OU conclusion.
- A low line does not automatically mean a genuinely low-event match; price around the line may indicate concentrated probability mass near the threshold.

## 11. Cross-market coherence — ACTIVE

- 1X2, AH and OU are linked prices, not three independent votes.
- Test whether they imply compatible match paths.
- Conflicts are information and must be explained, not hidden by averaging.
- Stage14 market reconstruction is not independent confirmation of the same market inputs.

## 12. Market attraction / favourite failure — ACTIVE

- Assess favourite heat and underdog betting story/public attraction before interpreting weak-side protection.
- Strong favourites require favourite-win vs favourite-non-win decomposition.
- Favourite non-win = draw + underdog outright win.
- Explicitly determine whether favourite failure is draw-led or underdog-win-led.
- Weak-side non-lowering odds do not automatically mean rejection when the weak side lacks public attraction.
- Hot favourite narratives require a favourite-tax audit; this is not automatic evidence to oppose the favourite.

## 13. External draw-exclusion website — ONE-MONTH HARD TEST

Test start: 2026-09-09.
Authoritative source: `draw_exclusion/latest.json` -> referenced `draw_exclusion/daily/YYYY-MM-DD.json`.
Legacy research labels are not the execution source.

Market isolation: query `draw_exclusion/index.json` separately through
`by_market.JC.by_titan_match_id` and `by_market.BD.by_titan_match_id`.
JC is PRIMARY_LAYER; BD is SECONDARY_VALIDATION_LAYER. All execution rules in
this section apply to JC only. JC=1/BD=1 strengthens the signal; JC=1/BD=0
follows JC with BD counterevidence; JC=0/BD=1 does not exclude and records a BD
risk hint; JC=0/BD=0 has no exclusion signal. Missing JC remains UNKNOWN even
when BD excludes. Keep both layers' labels and evidence independently.

### EXCLUDED = 1

- Hard execution constraint for this one-month test.
- Do not independently veto/reopen whether the website should exclude draw.
- Remove draw immediately from the execution branch.
- Immediately open HOME WIN vs AWAY WIN audit.
- Then determine favourite cover / favourite win-no-cover / underdog outright upset.
- Actual draw outcome is still preserved after the match for prospective website validation.

### NOT_EXCLUDED = 0

- Does not mean the website predicts draw.
- Draw stays active and receives enhanced mandatory audit: WH/Lad draw position, all core-company de-vig draw probabilities, opening-to-current draw lifecycle, same-time draw divergence, AH/1X2/OU coherence, score-grid draw mass and draw-compatible scores.
- Stage-17 falsification must test whether draw is the leading favourite-failure path and whether a proposed deep-AH ticket survives it.

### UNKNOWN / missing

- Missing/absent/null stays UNKNOWN.
- Never coerce missing into NOT_EXCLUDED.

## 14. Underdog outright audit — ACTIVE

Mandatory for favourites -0.75 and deeper, and central in winner-only review after hard draw exclusion.

- Start from the independent fundamental baseline.
- Low absolute underdog win probability is normal and is not evidence against an upset.
- Compare Titan WH, Ladbrokes, Bet365, Pinnacle, Interwetten, Macau and HKJC weak-side outright prices after de-vigging.
- Use closest same-time slices.
- Separate structural opening divergence from later divergence expansion.
- Compare company residual versus match median; where calibrated, compare abnormal residual versus the company's normal league/handicap bias.
- Inspect AH deepening with weak-side outright protection, AH retreat with weak-side strengthening, two-ended win-tail strengthening, same-company AH+1X2 protection and independent company clusters.
- Never convert +AH support into outright-upset evidence without 1X2 support.
- U0/U1/U2/U3 = upset-evidence quality, not absolute underdog probability.
- Stage-17 falsification must explicitly ask whether the analysis is inventing reasons for the favourite while ignoring weak-side outright pricing.

## 15. Correct score — ACTIVE

- Use repository Poisson/Dixon-Coles joint distribution plus Bayesian/context update.
- Maximum final Top3 scorelines, preserving Top1/Top2/Top3 order.
- Every score must pass final 1X2/AH/OU direction-consistency gate.
- Deep favourite cover conclusions must downgrade non-cover scores like 1-0/2-1/3-2 unless the final AH view explicitly allows them.
- Account for 5+ team-goal tail in deep-handicap/high-total matches.
- Never reconstruct or re-rank score candidates after seeing the result.

## 16. Data / crawler / missingness — ACTIVE

- Titan match_id is the preferred unique match key; ID correctness outranks displayed naming inconsistency.
- Deep crawler preserves 1X2/AH/OU/OU ladder, timestamps, MAIN/ALT, raw_text and QC.
- PREDICTED and CONFIRMED lineups must never be conflated.
- If WH/Lad/Pinnacle/Interwetten/Bet365 or another key company lacks a verifiable timeline, name the missing company/match explicitly.
- Opening/current values must not be presented as a full timeline.
- Titan blank timeline may be interface/API failure; report MISSING rather than fabricate.

Quick-scan crawler core companies remain exactly HKJC / Macau / WH / Ladbrokes / Interwetten. Pinnacle/Bet365/Crown enter deep analysis.

## 17. Quick scan — ACTIVE

- Only pre-match first-tier events; started/finished/postponed/interrupted/cancelled excluded.
- Use Beijing time plus Titan state.
- Target around five hours before kickoff.
- Quick scan is match selection, not final deep analysis.
- High-profile Champions League/major events are not dropped merely because structure is unclear; retain a direction plus structure grade for later selection.
- Candidate can be AH or OU depending on the cleanest chain.

## 18. Mandatory shadow/research checks — ACTIVE CHECK, ZERO FORMAL WEIGHT

When the user says `按Model_1分析`, force-check both modules even if out of scope.

### Team Goal Baseline

- Research/audit layer only.
- Strict no-future-leakage.
- Must not be double-counted as an independent prior beside another historical prior.
- If unavailable, output `MISSING_RUNTIME` / `OUT_OF_SCOPE` rather than inventing λ.
- Formal ticket weight remains NONE unless separately activated.

### Prematch Context / Recent Form V1

- SHADOW calibration layer.
- Formal weight NONE unless a competition-specific artifact has passed activation criteria.
- Narrative claims cannot be arbitrary ±λ updates.
- Missing competition calibration must be disclosed.

## 19. Macau post-2026-09-01 regime hypothesis — RESEARCH ONLY

- Preserve all post-2026-09-01 crawler files, including ordinary/uninteresting samples.
- >=2026-09-01 = Candidate New Regime; earlier = Control/Old Regime.
- Preserve real opening times and synchronized AH/1X2/OU movement.
- Do not let this hypothesis change formal MODEL_1 tickets before prospective validation.

## 20. Drift / anti-rationalization mode — ACTIVE

As of 2026-09-16 the user has identified a multi-match period in which MODEL_1 analysis appeared systematically off-course. Treat this as a process-risk state, not one isolated bad match.

Primary hypotheses to audit prospectively:

1. H1 anchoring — later modules organize around the first direction.
2. Market-explanation drift — explaining why movement occurred instead of testing whether the interpretation is correct.
3. Weak adversarial function — the old Red Team/H2 layer often acted as procedural confirmation.
4. MARKET_ONLY over-reliance — market-derived scoring can overstate independence from the same market evidence.
5. OU/score center anchoring — market center may dominate tails/event volatility.
6. Correlated directional errors — repeated misses of the same structural type matter more than a generic losing streak.

Current remedy is process correction, not small-sample numeric retuning:

- mandatory H2 removed;
- single-H1 falsification hard gate activated;
- repeated correlated errors default to model/execution failure until disproven;
- no post-result excuse-first behavior;
- no result-aware reconstruction of pre-match signals.

## 21. User challenge layer — SHADOW DIAGNOSTIC

- Formal weight = NONE.
- User disagreement does not automatically flip the ticket.
- When the user gives a reason for rejecting the model, preserve the reason as a prospective diagnostic signal.
- Real-money testing is not required.
- The objective is to identify recurring omitted variables or logic failures, not to prove that 'always betting opposite' is a strategy.
- If a recurring challenge pattern survives a sufficient prospective sample, research it as a future candidate module rather than silently changing MODEL_1 weights.

## 22. Recent diagnostic lesson: Rayo Vallecano vs Espanyol

The pre-match model supported Espanyol +0.25 and Under 2.5; during the match Rayo reached an early 2-0 lead. The diagnostic lesson is not 'an early goal happened'. The pre-match process risk was:

- over-reading the AH retreat from Rayo -0.5 toward -0.25/PK as home-side weakening;
- seeing late synchronized Rayo 1X2 buyback but not allowing it to reopen the thesis strongly enough;
- treating the low OU structure too confidently as a low-event match;
- allowing later modules to reinforce the weak-side H1 instead of genuinely challenging the lifecycle interpretation.

This case is the canonical warning for **explaining the market instead of testing the market interpretation**. Do not convert the live state into final settled statistics until the match is final.

## 23. Preflight hard gate — ACTIVE

`gpt/preflight_gate.py` version 1.2+ no longer requires:

- H2 candidate;
- H2 blindness protocol;
- H1-vs-H2 equal-status adjudication.

It now requires, among other existing checks:

- neutral evidence ledger;
- H1 contradictions;
- explicit H1 failure conditions;
- counterevidence tested;
- alternative match paths tested;
- market-rationalization guard;
- competition-rules gate when relevant;
- single-H1 falsification completed;
- final direction survives falsification;
- if overturned, old H1 discarded and rebuilt H1 rechecked.

Missing any hard requirement => `PRECHECK_BLOCKED_NO_TICKET`.
