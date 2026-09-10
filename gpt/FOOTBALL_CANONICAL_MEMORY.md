# Football Canonical Memory — MODEL_1 Frozen Active Rules

Snapshot date: 2026-09-10 Beijing time
Default model: `MODEL_1`
Registry: `config/model_registry.json`
Freeze contract: `config/model_1_freeze.json`

Purpose: keep the user's active cross-chat football rules in one auditable GitHub source so future analysis does not depend on conversational recall. MODEL_1 is the first/default formal model. If future win rate is unsatisfactory, preserve MODEL_1 and create MODEL_2/3/etc; never silently overwrite MODEL_1 history.

## 1. Authority / versioning

- GitHub `luccawong/football-model` is the canonical rule source.
- Chat memory is auxiliary; a new explicit user instruction takes precedence until GitHub is updated.
- Rule changes apply prospectively. Do not rewrite old pre-match decisions after results.
- Once an actionable formal ticket is issued, it is LOCKED. Later change must be an explicit correction `old -> new`.
- Separate fact / inference / assumption / conclusion and actively challenge both user and model hypotheses.
- From 2026-09-10 through 2026-10-10 Beijing time, MODEL_1 formal semantics are frozen unless the user explicitly ends the freeze.

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
15. Uncertainty audit
16. Freeze H1
17. Independent Red Team H2
18. Formal main ticket

Quick scan is only match selection and never substitutes for this deep-analysis sequence.

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

## 11. Cross-market coherence — ACTIVE

- 1X2, AH and OU are linked prices, not three independent votes.
- Test whether they imply compatible match paths.
- Conflicts are information and must be explained, not hidden by averaging.

## 12. Market attraction / favourite failure — ACTIVE

- Assess favourite heat and underdog betting story/public attraction before interpreting weak-side protection.
- Strong favourites require favourite-win vs favourite-non-win decomposition.
- Favourite non-win = draw + underdog outright win.
- Explicitly determine whether favourite failure is draw-led or underdog-win-led.
- Weak-side non-lowering odds do not automatically mean rejection when the weak side lacks public attraction.

## 13. External draw-exclusion website — ONE-MONTH HARD TEST

Test start: 2026-09-09.
Authoritative source: `draw_exclusion/latest.json` -> referenced `draw_exclusion/daily/YYYY-MM-DD.json`.
Legacy research labels are not the execution source.

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
- Red Team must test whether draw is the leading favourite-failure path and whether a proposed deep-AH ticket survives it.

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
- Red Team must explicitly ask whether the analysis is inventing reasons for the favourite while ignoring weak-side outright pricing.

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

## 18. Macau post-2026-09-01 regime hypothesis — RESEARCH ONLY

- Preserve all post-2026-09-01 crawler files, including ordinary/uninteresting samples.
- >=2026-09-01 = Candidate New Regime; earlier = Control/Old Regime.
- Preserve real opening times and synchronized AH/1X2/OU movement.
- Do not let this hypothesis change formal MODEL_1 tickets before prospective validation.

## 19. Betfair / OddsPapi Exchange — SHADOW ONLY

- OddsPapi genuine Betfair Exchange only; Titan Betfair-labelled rows are not a substitute.
- `formal_system_impact = false`.
- Freeze formal MODEL_1 Baseline before Exchange Shadow.
- Single Back/Lay snapshot is not smart money.
- runner tradedVolume is unsigned cumulative data, not signed flow.
- Do not sum runner tradedVolume and call it market total matched.
- Missing deep fields remain MISSING.
- Exchange shadow is excluded from formal ticket changes and formal statistics.

## 20. Probability / price — ACTIVE

- League/event probability is prior/risk filter, not standalone single-match edge.
- Do not let obvious strong-team base probability dominate company-pricing analysis.
- User generally wants decimal odds around >=1.80; exact minimum may be stated per ticket.
- Do not reject a stable direction solely because value/EV is thin.
- Distinguish payout/EV-only price changes from information changes that alter the match path.

## 21. Chinese football — ACTIVE separation

- Chinese competitions use a separate research/calibration pool.
- Do not blindly transfer overseas calibration.
- Performance ledger may remain unified: research pool separate, record statistics combined.

## 22. Post-match diagnostics — ACTIVE

- Do not change MODEL_1 from a few isolated outcomes.
- First diagnose model logic, missing/late data, selection bias, time-axis interpretation, lineup error, market anomaly, off-field miss or other cause.
- Mandatory deep-favourite upset review after a favourite -0.5 or deeper fails.
- Never backfill pre-match evidence after results.

## 23. Statistics / record workflow — ACTIVE

- Analysis chat does not update the central stats source.
- `记录/存档` = freeze pre-match final version only.
- Only explicit `统一纳入表格 / 统一更新统计表 / 现在更新母表` authorizes batch central write.
- Database = fact source; Excel = report/output layer.
- Preserve correct-score Top1/Top2/Top3 with the frozen pre-match record.
- Formal model accuracy is primary; user's actual bet/stake/P&L are separate secondary fields.

## 24. Reasoning discipline — ACTIVE

- Do not agree reflexively.
- Check wrong premises, logic jumps, concept switching and missing information.
- Distinguish fact / forecast / assumption / subjective view.
- If disagreeing, state it with evidence, counterexamples, boundary conditions and alternative explanations.
- Check sampling bias, causal leaps and post-hoc rationalization.

## 25. Model-freeze discipline — ACTIVE

From 2026-09-10 through 2026-10-10 Beijing time:

- no new formal modules;
- no new formal weights or threshold tuning;
- no promotion of research/shadow features;
- no stage reorder;
- no change to Titan-only source authority, draw hard-test, ticket policy or Red Team semantics;
- new ideas are logged only for later MODEL_2 consideration.

Allowed maintenance: parser/runtime/data-identity/QC bug fixes that restore the frozen semantics, tests, raw-data collection, result/statistics updates and documentation corrections that merely align stale text with the frozen policy.

## 26. Superseded — DO NOT EXECUTE

- Formal main / unique non-main / PASS policy -> superseded. MODEL_1 = exactly one formal main, no non-main, no final PASS.
- Immediate central-table write on `记录` -> superseded by freeze-first workflow.
- Betfair formal ticket authority -> superseded by SHADOW_ONLY.
- Legacy draw-exclusion research label as execution source -> superseded by `draw_exclusion/latest.json` -> daily file.
- Old full-analysis order with market snapshot before fundamentals -> superseded by MODEL_1 order above.
- Any rule allowing JCB/Sporttery as current auxiliary input -> superseded; both are disabled for MODEL_1.

## 27. Runtime / implementation

MODEL_1 is encoded beyond prose:

- `config/model_registry.json` — selects MODEL_1 and records freeze status.
- `models/MODEL_1_DEFAULT.md` — frozen model profile.
- `config/active_decision_policy.json` — machine-readable hard policy + 18-stage order.
- `config/off_field_weather_policy.json` — Stage 5 environment/psychology policy.
- `config/model_1_freeze.json` — one-month formal freeze contract.
- `config/module_registry.json` — modules mapped to MODEL_1 stages.
- `config/model_1_trace_contract.json` — mandatory 18-stage trace evidence fields.
- `gpt/decision_engine.py` — policy validator.
- `gpt/formal_trace.py` — frozen pre-match trace serializer/validator.
- `gpt/GPT_RUNTIME.md` and `gpt/MANIFEST.json` — cross-chat runtime/manifest.
