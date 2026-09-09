# Football Canonical Memory — Active Rules Snapshot

Snapshot date: 2026-09-09

Purpose: migrate the user's cross-chat football-model rules into one auditable GitHub reference so runtime decisions do not depend on chat memory alone. This file distinguishes ACTIVE rules, RESEARCH/SHADOW rules, and SUPERSEDED/CONFLICT items that must not silently drive analysis.

## 1. Authority and versioning

- GitHub repository `luccawong/football-model` is the canonical football-model rule source.
- Chat memory is auxiliary context only. If chat memory and the current GitHub formal rule conflict, use the current GitHub rule unless the user explicitly says to modify the model.
- Rule changes must be versioned prospectively. Do not rewrite old pre-match decisions after results.
- Once an actionable formal ticket is sent, it is LOCKED. Any later change must be explicitly labeled as a correction with old -> new; silent direction/grade changes are forbidden.
- Facts, inference, assumptions and conclusions must be separated. The model must actively challenge user hypotheses and its own first-pass narrative.

## 2. Current output / ticket policy — ACTIVE and newest

- Every analyzed match must produce exactly ONE formal main ticket.
- There are NO non-main tickets.
- Do not output a separate non-main strategy layer.
- Do not use PASS as the final match output during the current policy regime; choose the best available formal main direction and grade it honestly, including low grades where appropriate.
- Near kickoff, output the formal ticket first: market + handicap/line + grade + actionable reference price + one-line core logic. Full reasoning follows.
- Formal ticket accuracy is the primary performance metric; the user's personal bet/no-bet status is separate from model correctness.

## 3. Full analysis order — ACTIVE

Deep analysis must follow this order without compressing modules:

1. Market snapshot / Data Gate
2. Opening-line first impression
3. Opening validity / odds lifecycle
4. Off-field scan
5. Fundamentals / strength prior
6. Squad / lineup / tactical audit
7. Schedule and future-priority audit
8. 1X2 company pricing and same-time-slice divergence
9. Asian handicap lifecycle
10. Independent totals / OU
11. Cross-market coherence
12. Market attraction + favourite-failure decomposition
13. Mandatory underdog outright audit when favourite handicap is -0.75 or deeper
14. Draw-exclusion website layer and enhanced draw audit
15. Correct-score layer
16. Uncertainty audit
17. Freeze H1
18. Independent Red Team H2
19. Final formal main ticket

Quick scan is only for match selection and must never substitute for deep analysis.

## 4. Opening interpretation and lifecycle — ACTIVE

- Opening first impression uses OPENING STRUCTURE ONLY. Later injuries, lineups, schedule, motivation, weather and movement must not contaminate the opening read.
- Later information belongs in the later context layer and later price changes must be explained as movement/repricing logic.
- Distinguish true opening, information re-opening after intervening matches/news, and ordinary market movement.
- If an opening quote was posted days earlier and the team played another match after that quote, assess whether the original opening remains a valid anchor.
- Never compare companies' first visible quotes directly when they were posted at materially different times. Align to the closest common time slice first.

## 5. 1X2 company roles — ACTIVE

Mandatory core company audit:

- William Hill + Ladbrokes: primary reference pair.
- William Hill: draw-price position, draw protection/prevention/inducement.
- Ladbrokes: home/away win-loss difference and relative tail pricing.
- Interwetten: cold-side / upset-risk check.
- Pinnacle: capital/market anchor, but NOT automatically 'smart money'.
- Macau: Asian-market signal and cross-market divergence.
- Bet365: major comparator and retail/popularity-sensitive reference.
- HKJC: important local/Asian comparator when available.

For each relevant time slice:

- preserve the real European odds (e.g. 2.55 / 3.60 / 2.63);
- separately compute de-vig H/D/A probabilities;
- report percentage-point company differences;
- never call de-vig probabilities 'European odds'.

Do not conclude 'lower favourite price = favourite wins'. The main edge is cross-company pricing divergence and its lifecycle.

## 6. Favourite failure decomposition — ACTIVE

For strong favourites / obvious hot sides:

- analyse favourite win vs favourite non-win;
- favourite non-win = draw + underdog win;
- explicitly determine whether the non-win path is draw-led or underdog-win-led;
- market attraction is a prerequisite variable: assess whether the underdog has a strong betting story or weak public attraction;
- weak-side non-lowering odds do not automatically mean rejection if the weak side lacks attraction.

## 7. External draw-exclusion website — ONE-MONTH HARD EXECUTION TEST

Test start: 2026-09-09.

Authoritative source:

`draw_exclusion/latest.json` -> referenced `draw_exclusion/daily/YYYY-MM-DD.json`

Do NOT substitute legacy `research/paiping_labels` as the execution source.

### EXCLUDED = 1

- Treat the website's draw exclusion as a HARD execution constraint for the current one-month test.
- Do NOT independently veto or reopen whether the match should be draw-excluded.
- Remove draw from the execution branch.
- Analyse HOME WIN vs AWAY WIN only, then decide favourite cover / favourite win-no-cover / underdog outright upset.
- Research records must still preserve the real draw outcome after the match for prospective validation.

### NOT_EXCLUDED = 0

- This does NOT mean the website predicts a draw.
- Draw remains an active path and must receive an ENHANCED mandatory audit before the final ticket.
- Audit WH/Lad draw pricing, all core-company de-vig draw probabilities, opening-to-current draw lifecycle, same-time-slice divergence, AH/1X2/OU coherence and draw-compatible score mass.
- Red Team must explicitly test whether draw is the leading favourite-failure path and whether the proposed handicap ticket survives that draw path.
- A deep favourite cannot be justified only by a high favourite win probability.

### UNKNOWN / missing

- If the match is absent from the verified daily pool, or the label is NULL/UNKNOWN, keep it UNKNOWN.
- Never coerce missing into NOT_EXCLUDED.

## 8. Mandatory Underdog Outright Audit — ACTIVE

Trigger: favourite handicap deeper than -0.5, i.e. -0.75 and beyond.

Purpose: correct the historical bias of explaining why a strong favourite should win while treating the weak side only as an AH-cover candidate.

Rules:

- Start from an independent fundamental baseline.
- Low absolute underdog outright probability is normal and is NOT itself evidence against an upset.
- Compare WH, Ladbrokes, Bet365, Pinnacle, Interwetten, Macau and HKJC underdog-out-right prices after de-vigging.
- Use closest same-time slices.
- Separate structural opening divergence from later divergence expansion.
- Compare each company versus the same-match company median; where historical calibration exists, also compare versus that company's normal bias for the same league/handicap bucket.
- Inspect specifically:
  - AH deepens while underdog outright probability refuses to fall;
  - AH deepens while underdog outright probability rises;
  - AH retreats while underdog outright probability rises;
  - favourite win and underdog win tails strengthen while draw is compressed;
  - one company protects the underdog in both AH and 1X2;
  - multiple independent company clusters protect the underdog outright.
- Never convert '+AH support' into an outright-upset claim without 1X2 evidence.
- U0/U1/U2/U3 grades reflect quality of outright-upset evidence, not the absolute underdog probability.
- Red Team must ask: 'Am I inventing reasons for the favourite while ignoring weak-side outright pricing evidence?'

Working interpretation:

- U0: no abnormal underdog outright divergence.
- U1: one-company / weak isolated protection.
- U2: at least two independent companies form meaningful weak-side outright divergence.
- U3: multi-company divergence + lifecycle expansion + AH confirmation + plausible fundamental upset path.

These thresholds are descriptive until historical database calibration validates exact cutoffs.

## 9. Asian handicap — ACTIVE

- Read line AND water lifecycle, not current line alone.
- Check failed upgrades, reversals, and adjacent counterfactual lines.
- Favourite win probability is not the same as cover probability.
- Especially at -0.75 / -1 / -1.25 / -1.5+, audit separately:
  1. favourite wins and covers;
  2. favourite wins but does not cover;
  3. draw;
  4. underdog wins outright.
- Do not let strong 1X2 support automatically upgrade a deep AH ticket.

## 10. Totals / OU — ACTIVE

- Totals is a separate core module and must be decided independently after 1X2/AH.
- Never mechanically infer Over/Under from the AH side.
- WH/Ladbrokes fixed 2.5 is a Base-2.5 probability anchor, not a dynamic-main-line comparator.
- Dynamic mainstream OU is primarily Macau + Pinnacle + Bet365.
- If companies display different OU line levels, convert line + price / alternate ladder to a comparable latent total distribution before calling it real disagreement.
- A large line-level gap alone may be display/ladder-selection difference, not information edge.
- JCB/Sporttery goal-count data, when explicitly available in analysis context, is auxiliary confirmation only and never the primary totals decision source.

## 11. Correct score — ACTIVE

- Use Poisson/Dixon-Coles style joint distribution plus Bayesian/context update; no lazy score guessing.
- Maximum final Top3 scorelines.
- Every score candidate must pass direction-consistency with final 1X2, AH and OU conclusions.
- If final direction is a favourite covering -1 or deeper, downgrade 1-0 / 2-1 / 3-2 type non-cover paths unless the final handicap conclusion itself allows them.
- For deep handicaps/high totals, account for 5+ team-goal tail even if a source table truncates at four.

## 12. Off-field / relationship / schedule layer — ACTIVE

Mandatory checks include:

- official club/league announcements first;
- then major European sports media and beat/insider reporting including Marca, L'Equipe and Sky Sports where relevant;
- rumours/insider claims must be labeled as hypotheses unless verified;
- common/related ownership and multi-club groups;
- management/coaching/agent networks;
- frequent loans/transfers, academy/satellite relationships;
- local political/business ties;
- historical friendly/hostile relationships;
- relegation/title/Europe qualification incentive reciprocity;
- 'needs points' end-of-season incentives;
- future 7-10 day schedule priority, not only past rest;
- next high-priority Champions League/Europa/cup/derby/title match;
- rotation probability, expected core minutes, travel burden, squad depth and leading-game tempo reduction.

Schedule pressure primarily affects deep-cover ability and score tail; it must not be mechanically translated into 'favourite cannot win'.

Daily same-day off-field digest should be incorporated as a context layer, but later official lineups/club announcements override earlier reporting when contradictory.

## 13. Macau post-2026-09-01 regime hypothesis — RESEARCH ONLY

- Preserve all football crawler files from 2026-09-01 onward; do not delete uninteresting/PASS-like samples.
- Label 2026-09-01 onward as Candidate New Regime and pre-2026-09-01 as Control/Old Regime.
- Preserve Macau real opening time, each change time, synchronized AH/1X2/OU paths.
- Do not modify formal ticket logic merely because of the regime hypothesis.
- Compare opening depth, lead-lag, favourite treatment, weak-side protection, draw pricing, OU ladders and actual results prospectively.
- After sufficient samples, matched comparison should control league, line bucket and favourite strength.
- Especially useful Macau divergences should be flagged as research samples.

## 14. Betfair / OddsPapi Exchange — SHADOW ONLY

Current formal authority:

- OddsPapi is used for genuine Betfair Exchange data.
- Titan rows named Betfair are NOT OddsPapi Exchange and must not be treated as such.
- Exchange is SHADOW_RESEARCH only; `formal_system_impact = false`.
- Freeze the non-Exchange baseline first, then run Exchange shadow increment.
- Single current Back/Lay snapshot is not smart money.
- Runner `tradedVolume` is cumulative and unsigned; it is not signed order flow.
- Do not sum runner tradedVolume and call it market total matched.
- `total_matched`, traded ladder, matched trade-side direction and deep depth remain MISSING unless explicitly returned.
- Missing Exchange data is not negative evidence and must not force a downgrade.
- Exchange shadow results are excluded from formal statistics.
- Do not use a single Exchange rule to create/upgrade/overturn the formal ticket.

Research goal: compare baseline-vs-shadow on the same sample and measure errors corrected versus errors introduced before granting formal authority.

## 15. Price / execution — ACTIVE

- User generally wants decimal odds around >=1.80 for long-run execution; exact minimum may be stated per ticket.
- Do not reject a stable direction solely because EV/value is thin.
- Separate price changes into:
  1. payout/EV change only, direction unchanged;
  2. information change that alters market structure/path and can justify correction.
- Only type (2) should materially alter the direction.

## 16. Data / crawler / missingness — ACTIVE

- Titan match_id is the preferred unique match key; when user gives team/date/league, match_index should resolve ID automatically.
- ID correctness has priority over displayed naming inconsistencies.
- Deep crawler should preserve 1X2, AH, OU, OU ladder/alternate lines, timestamps, MAIN/ALT, raw_text and QC fields.
- Starting lineup/formation must be captured when Titan provides it, including image/DOM-derived lineup structures.
- PREDICTED and CONFIRMED lineups must never be conflated.
- If WH, Ladbrokes, Pinnacle, Interwetten, Bet365 or another key company lacks a verifiable detailed timeline, explicitly name the missing company/match. Opening/current values must not be presented as if they were a full timeline.
- A blank Titan timeline can be a Titan interface/API issue and must be reported as missing rather than fabricated.
- Missing data stays MISSING; no silent fill.

Quick-scan crawler core companies remain exactly:

- HKJC
- Macau
- William Hill
- Ladbrokes
- Interwetten

Pinnacle/Bet365/Crown and others belong in deep analysis, not the first quick-scan sheet.

## 17. Quick scan — ACTIVE

- Scope: pre-match first-tier events only; started/finished/postponed/interrupted/cancelled excluded.
- Use Beijing time against kickoff in addition to Titan state markers.
- Target timing is around five hours before kickoff.
- Quick scan uses opening/early information only and is not a final bet.
- For Champions League / other high-profile events, do not drop a match merely because structure is unclear; give a direction/structure grade for selection.
- Candidate direction may be AH or totals, whichever has the cleanest evidence chain.

## 18. Probability role — ACTIVE

- League/event historical probability is a baseline prior or risk filter, not a standalone single-match betting edge.
- Example: if a league is structurally high-scoring, avoid casual unders without strong contrary evidence.
- Do not let obvious team-strength probabilities dominate the analysis; the core remains company pricing divergence and market structure.

## 19. Chinese football research — ACTIVE separation rule

- Chinese competitions (CSL, China League One/Two, FA Cup etc.) must use a separate research/calibration pool.
- Do not transfer overseas calibration blindly into Chinese football.
- Central overall performance reporting may still aggregate competitions; 'research pool separate, performance ledger unified'.

## 20. Post-match diagnostics — ACTIVE

- Do not change the core model after a few isolated losses.
- Run an independent diagnostic layer first: model logic, missing/late data, selection bias, time-axis interpretation, lineup error, market anomaly, off-field miss or other cause.
- Mandatory deep-favourite upset review after a favourite -0.5 or deeper fails, especially home -0.5/-0.75/-1 and deeper.
- Never backfill pre-match features using the final result.

## 21. Statistics / record workflow — ACTIVE

- Analysis chats prioritize analysis and ticket speed; do not update the central workbook/database during pre-match analysis.
- A user message like '记录/存档' freezes the pre-match final version; it does not automatically write/update the central statistical workbook unless the user explicitly requests a unified update.
- Only explicit instructions equivalent to '统一纳入表格 / 统一更新统计表 / 现在更新母表' authorize batch write to the current central statistics source.
- Database is the preferred factual source; Excel is an output/report layer.
- Correct-score Top1/Top2/Top3 should be preserved with the frozen pre-match record for later settlement.
- Settlement colors in Excel: full/half win green; full/half loss red; push/void white.

## 22. Interaction / reasoning discipline — ACTIVE

- Do not agree reflexively with the user.
- Before analysis, check for wrong premises, logic jumps, concept switching and missing information.
- Distinguish facts, forecasts/inference, assumptions and subjective views.
- If disagreeing, state it directly with evidence, counterexamples, boundary conditions and alternative explanations.
- Explicitly check sampling bias, causal leaps and after-the-fact rationalization.

## 23. SUPERSEDED / do not execute

The following older rules are superseded by newer user instructions and must not silently reactivate:

- 'Formal main or unique non-main/PASS' -> SUPERSEDED. Current rule is exactly one formal main ticket per match; no non-main ticket; no final PASS.
- 'If there is a formal main, no non-main; otherwise give one non-main' -> SUPERSEDED.
- Any prior statistics workflow that writes the central workbook immediately when the user says only 'record' -> SUPERSEDED by the freeze-first / unified-update-only rule.
- Any Betfair mode that allows Exchange to alter formal ticket/grade during the current shadow test -> SUPERSEDED by SHADOW_ONLY.
- Legacy draw-exclusion research labels as execution source -> SUPERSEDED by `draw_exclusion/latest.json` -> daily file.

## 24. OPEN CONFLICT / USER REVIEW REQUIRED

These are intentionally NOT silently resolved; user should inspect:

1. JCB/Sporttery: chat-analysis memory says use JCB/Sporttery only as auxiliary context when explicitly supplied, while an older software-V2 decision removed Sporttery from the V2 product/interface. Proposed interpretation: keep JCB out of the V2 software runtime, but allow it as optional external auxiliary context in ChatGPT analysis when user supplies it. USER TO CONFIRM.
2. 'Every match must have a formal main ticket' removes PASS entirely. This snapshot treats that as the newest hard rule, including low-confidence matches receiving a low-grade main direction. USER TO CONFIRM whether any emergency data-integrity exception should exist for identity mismatch/corrupt data; current wording says no final PASS.
3. Quick-scan and deep-analysis ticket policy: this snapshot assumes the 'exactly one formal main' requirement applies to every match that receives full analysis, not every raw quick-scan candidate. USER TO CONFIRM.

## 25. Runtime loading order

For future football analysis, preferred rule-loading order is:

1. `gpt/FOOTBALL_CANONICAL_MEMORY.md`
2. `gpt/FOOTBALL_SOP.md`
3. `config/active_decision_policy.json`
4. `config/full_stack_config.json`
5. `config/module_registry.json`
6. dedicated Exchange / draw-exclusion rule files

If a lower file conflicts with the newest explicit user policy above, flag the conflict and update the repository rather than silently choosing the older rule.
