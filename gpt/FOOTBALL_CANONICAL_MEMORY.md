# Football Canonical Memory — MODEL_1 Active Rules

Snapshot date: 2026-09-09
Default model: `MODEL_1`
Registry: `config/model_registry.json`

Purpose: keep the user's active cross-chat football rules in one auditable GitHub source so future analysis does not depend on conversational recall. MODEL_1 is the first/default formal model. If future win rate is unsatisfactory, freeze MODEL_1 and create MODEL_2/3/etc; never silently overwrite MODEL_1 history.

## 1. Authority / versioning

- GitHub `luccawong/football-model` is the canonical rule source.
- Chat memory is auxiliary; a new explicit user instruction takes precedence until GitHub is updated.
- Rule changes apply prospectively. Do not rewrite old pre-match decisions after results.
- Once an actionable formal ticket is issued, it is LOCKED. Later change must be an explicit correction `old -> new`.
- Separate fact / inference / assumption / conclusion and actively challenge both user and model hypotheses.

## 2. MODEL_1 ticket policy — ACTIVE

- Every fully analysed match produces exactly ONE formal main ticket.
- No non-main tickets.
- No final PASS in MODEL_1; uncertainty is expressed through grade and execution conditions.
- Near kickoff: ticket first = market/line + grade + actionable reference price + one-line logic; explanation follows.
- Formal ticket correctness is the primary model performance metric; user's personal bet/no-bet is separate.

## 3. MODEL_1 mandatory full-analysis order — ACTIVE

1. **Fundamentals**
2. **Market snapshot**
3. **Opening first impression**
4. **Opening rationality / lifecycle**
5. **Off-field factors / weather**
6. **Lineup / tactics**
7. **1X2**, including post-fundamentals **实开 / 韬开** audit
8. **Asian handicap**, including explicit **欧亚转换** consistency after 1X2
9. **Totals / OU**
10. **Cross-market coherence**
11. **Market attraction**
12. **External draw-exclusion website**; if draw is excluded, immediately open HOME-vs-AWAY winner audit; if not excluded, run enhanced draw audit
13. **Underdog outright audit（下盘独赢）**
14. **Correct score** using repository Poisson / Dixon-Coles / Bayesian theory
15. **Uncertainty audit**
16. **Freeze H1**
17. **Independent Red Team H2**
18. **Formal main ticket**

Quick scan is only match selection and never substitutes for this deep-analysis sequence.

## 4. Fundamentals first — ACTIVE

Before market interpretation, review:

- recent matches one by one, not only aggregate W-D-L;
- who each win came against and who each loss came against;
- opponent quality: a win over a weak side is not equal to a win over a strong side; a narrow loss to an elite side is not equal to a loss to a weak side;
- how each result happened: margin, game state, home/away context, shots/xG/chance quality where available, whether the result was repeatable or flattering;
- recent head-to-head only with recency/context, not as a standalone causal rule;
- future 7–10 day schedule and priority pressure, including strength/importance of upcoming opponents;
- rotation/travel/expected core minutes and whether a favourite can economically win without covering a deep line.

Do not invent arbitrary numerical opponent-quality weights before calibration.

## 5. Opening interpretation / lifecycle — ACTIVE

- Opening first impression uses opening structure only. Later injuries, lineups, schedule, weather, motivation and movement must not contaminate it.
- Then distinguish true opening, information re-opening, and ordinary movement.
- If a quote was posted days earlier and the team played another match afterwards, reassess whether that opening is still a valid anchor.
- Companies whose first quotes are separated by days cannot be compared directly; align to the closest common time slice.

## 6. 1X2 + 实开 / 韬开 — ACTIVE

The real-open/camouflage-open audit runs only after fundamentals are established.

- Use fundamentals to assess whether the market broadly prices the true strength gap (`实开`) or contains a camouflage/hidden-pricing structure (`韬开`).
- This is a prior/diagnostic classification, NOT a mechanical result rule.
- Historical 实开/韬开 rules and AH×1X2 shortcut rules are priors only; they must not be mechanically applied to force a ticket.
- Cross-check classification against company divergence and lifecycle.

Mandatory company roles:

- William Hill + Ladbrokes = primary pair.
- WH = draw-price location / protection / inducement audit.
- Ladbrokes = home/away win-tail difference.
- Interwetten = cold-side / upset-risk check.
- Pinnacle = capital/market anchor, not automatic smart money.
- Macau = Asian signal and divergence.
- Bet365 = major comparator.
- HKJC = Asian/local comparator when available.

For relevant aligned time slices:

- preserve real European odds;
- separately compute de-vig H/D/A probabilities;
- report company percentage-point differences;
- never call de-vig probabilities 'European odds'.

Do not conclude `lower favourite price = favourite wins`.

## 7. AH + 欧亚转换 — ACTIVE

AH runs after 1X2.

- Explicitly test whether 1X2 strength/draw structure converts coherently into the AH line and water.
- Any 1X2-AH conflict must be explained, not averaged away.
- Read line + water lifecycle, failed upgrades, reversals and adjacent counterfactual lines.
- Favourite win probability is NOT the same as cover probability.
- For deep favourites, separate:
  1. favourite wins and covers;
  2. favourite wins but does not cover;
  3. draw;
  4. underdog wins outright.

## 8. Totals / OU — ACTIVE

- OU is a separate core module and must be determined independently from AH.
- Macau/Pinnacle/Bet365 = dynamic mainstream OU.
- WH/Lad fixed 2.5 = Base-2.5 probability anchor, not dynamic line-level comparator.
- Different displayed OU lines require line+price/alternate-ladder normalization to a comparable latent total distribution before calling company disagreement.
- JCB/Sporttery goal-count data, when explicitly supplied in analysis context, is auxiliary only and never primary OU evidence.

## 9. Cross-market coherence — ACTIVE

- 1X2, AH and OU are linked prices, not three independent votes.
- Test whether they imply compatible match paths.
- Conflicts are information and must be explained, not hidden by averaging.

## 10. Market attraction / favourite failure — ACTIVE

- Assess favourite heat and underdog betting story/public attraction before interpreting weak-side protection.
- Strong favourites require favourite-win vs favourite-non-win decomposition.
- Favourite non-win = draw + underdog outright win.
- Explicitly determine whether favourite failure is draw-led or underdog-win-led.
- Weak-side non-lowering odds do not automatically mean rejection when the weak side lacks public attraction.

## 11. External draw-exclusion website — ONE-MONTH HARD TEST

Test start: 2026-09-09.
Authoritative source: `draw_exclusion/latest.json` -> referenced `draw_exclusion/daily/YYYY-MM-DD.json`.
Legacy research labels are NOT the execution source.

### EXCLUDED = 1

- Hard execution constraint for this one-month test.
- Do NOT independently veto/reopen whether the website should exclude draw.
- Remove draw immediately from the execution branch.
- Immediately open **HOME WIN vs AWAY WIN** audit.
- Then determine favourite cover / favourite win-no-cover / underdog outright upset.
- Actual draw outcome is still preserved after the match for prospective website validation.

### NOT_EXCLUDED = 0

- Does NOT mean the website predicts draw.
- Draw stays active and receives enhanced mandatory audit:
  - WH/Lad draw position;
  - all core-company de-vig draw probabilities;
  - opening-to-current draw lifecycle;
  - same-time draw divergence;
  - AH/1X2/OU coherence;
  - score-grid draw mass and 0-0/1-1/2-2 paths where relevant.
- Red Team must test whether draw is the leading favourite-failure path and whether a proposed deep-AH ticket survives it.

### UNKNOWN / missing

- Missing/absent/null stays UNKNOWN.
- Never coerce missing into NOT_EXCLUDED.

## 12. Underdog outright audit — ACTIVE

Mandatory for favourites -0.75 and deeper, and central in winner-only review after hard draw exclusion.

- Start from the independent fundamental baseline.
- Low absolute underdog win probability is normal and is not evidence against an upset.
- Compare WH, Ladbrokes, Bet365, Pinnacle, Interwetten, Macau and HKJC weak-side outright prices after de-vigging.
- Use closest same-time slices.
- Separate structural opening divergence from later divergence expansion.
- Compare company residual versus match median; where calibrated, compare abnormal residual versus the company's normal league/handicap bias.
- Inspect:
  - AH deepens while underdog outright refuses to weaken;
  - AH deepens while underdog outright strengthens;
  - AH retreats while underdog outright strengthens;
  - favourite and underdog win tails strengthen while draw compresses;
  - same company protects weak side in AH and 1X2;
  - multiple independent clusters protect weak-side outright.
- Never convert +AH support into outright-upset evidence without 1X2 support.
- U0/U1/U2/U3 = upset-evidence quality, not absolute underdog probability.
- Red Team must explicitly ask whether the analysis is inventing reasons for the favourite while ignoring weak-side outright pricing.

## 13. Correct score — ACTIVE

- Use repository Poisson/Dixon-Coles joint distribution plus Bayesian/context update.
- Maximum final Top3 scorelines.
- Every score must pass final 1X2/AH/OU direction-consistency gate.
- Deep favourite cover conclusions must downgrade non-cover scores like 1-0/2-1/3-2 unless the final AH view explicitly allows them.
- Account for 5+ team-goal tail in deep-handicap/high-total matches.

## 14. Off-field / weather / relationship layer — ACTIVE

Priority:

1. official club/league / confirmed lineup;
2. same-day mainstream media and beat/insider reports;
3. earlier daily digest;
4. unverified rumours as hypotheses only.

Check, when relevant:

- weather/pitch/referee;
- common/related ownership or multi-club groups;
- management/coaching/agent networks;
- loans/transfers/academy/satellite relationships;
- local business/political ties;
- historical friendly/hostile relationships;
- relegation/title/Europe incentive reciprocity;
- future 7–10 day Champions League/Europa/cup/derby/title priorities;
- rotation, expected core minutes, travel, squad depth, leading-game tempo reduction.

Schedule pressure mainly affects deep-cover ability and score tail; do not mechanically translate it into favourite failure.

## 15. Data / crawler / missingness — ACTIVE

- Titan match_id is the preferred unique match key; ID correctness outranks displayed naming inconsistency.
- Deep crawler preserves 1X2/AH/OU/OU ladder, timestamps, MAIN/ALT, raw_text and QC.
- PREDICTED and CONFIRMED lineups must never be conflated.
- If WH/Lad/Pinnacle/Interwetten/Bet365 or another key company lacks a verifiable timeline, name the missing company/match explicitly.
- Opening/current values must not be presented as a full timeline.
- Titan blank timeline may be interface/API failure; report MISSING rather than fabricate.

Quick-scan crawler core companies remain exactly HKJC / Macau / WH / Ladbrokes / Interwetten. Pinnacle/Bet365/Crown enter deep analysis.

## 16. Quick scan — ACTIVE

- Only pre-match first-tier events; started/finished/postponed/interrupted/cancelled excluded.
- Use Beijing time plus Titan state.
- Target around five hours before kickoff.
- Quick scan is match selection, not final deep analysis.
- High-profile events should not be dropped merely because structure is unclear.
- Candidate can be AH or OU depending on the cleanest chain.

## 17. Macau post-2026-09-01 regime hypothesis — RESEARCH ONLY

- Preserve all post-2026-09-01 crawler files, including ordinary/uninteresting samples.
- >=2026-09-01 = Candidate New Regime; earlier = Control/Old Regime.
- Preserve real opening times and synchronized AH/1X2/OU movement.
- Do not let this hypothesis change formal MODEL_1 tickets before prospective validation.

## 18. Betfair / OddsPapi Exchange — SHADOW ONLY

- OddsPapi genuine Betfair Exchange only; Titan Betfair-labelled rows are not a substitute.
- `formal_system_impact = false`.
- Freeze formal MODEL_1 Baseline before Exchange Shadow.
- Single Back/Lay snapshot is not smart money.
- runner tradedVolume is unsigned cumulative data, not signed flow.
- Do not sum runner tradedVolume and call it market total matched.
- Missing deep fields remain MISSING.
- Exchange shadow is excluded from formal ticket changes and formal statistics.

## 19. Probability / price — ACTIVE

- League/event probability is prior/risk filter, not standalone single-match edge.
- Do not let obvious strong-team base probability dominate company-pricing analysis.
- User generally wants decimal odds around >=1.80; exact minimum may be stated per ticket.
- Do not reject a stable direction solely because value/EV is thin.
- Distinguish payout/EV-only price changes from information changes that alter the match path.

## 20. Chinese football — ACTIVE separation

- Chinese competitions use a separate research/calibration pool.
- Do not blindly transfer overseas calibration.
- Performance ledger may remain unified: research pool separate, record statistics combined.

## 21. Post-match diagnostics — ACTIVE

- Do not change MODEL_1 from a few isolated outcomes.
- First diagnose model logic, missing/late data, selection bias, time-axis interpretation, lineup error, market anomaly, off-field miss or other cause.
- Mandatory deep-favourite upset review after a favourite -0.5 or deeper fails.
- Never backfill pre-match evidence after results.

## 22. Statistics / record workflow — ACTIVE

- Analysis chat does not update the central stats source.
- `记录/存档` = freeze pre-match final version only.
- Only explicit `统一纳入表格 / 统一更新统计表 / 现在更新母表` authorizes batch central write.
- Database = fact source; Excel = report/output layer.
- Preserve correct-score Top1/Top2/Top3 with the frozen pre-match record.

## 23. Reasoning discipline — ACTIVE

- Do not agree reflexively.
- Check wrong premises, logic jumps, concept switching and missing information.
- Distinguish fact / forecast / assumption / subjective view.
- If disagreeing, state it with evidence, counterexamples, boundary conditions and alternative explanations.
- Check sampling bias, causal leaps and post-hoc rationalization.

## 24. Superseded — DO NOT EXECUTE

- Formal main / unique non-main / PASS policy -> superseded. MODEL_1 = exactly one formal main, no non-main, no final PASS.
- Immediate central-table write on `记录` -> superseded by freeze-first workflow.
- Betfair formal ticket authority -> superseded by SHADOW_ONLY.
- Legacy draw-exclusion research label as execution source -> superseded by `draw_exclusion/latest.json` -> daily file.
- Old full-analysis order with market snapshot before fundamentals -> superseded by MODEL_1 order above.

## 25. Runtime / second-step implementation

MODEL_1 is now encoded beyond prose:

- `config/model_registry.json` — selects MODEL_1 as default and protects future model identities.
- `models/MODEL_1_DEFAULT.md` — frozen model profile.
- `config/active_decision_policy.json` — machine-readable hard policy + 18-stage order.
- `config/module_registry.json` — modules mapped to the MODEL_1 stages.
- `gpt/decision_engine.py` — deterministic policy validator for stage order, draw branch, underdog audit, Red Team verdict and exactly-one-main output.
- `tests/test_decision_engine.py` — policy tests.
- `gpt/GPT_RUNTIME.md` — cross-chat runtime order.
- `gpt/MANIFEST.json` — default model/engine manifest.

## 26. Open item for user review

JCB/Sporttery scope remains interpreted as: not required in the core software runtime, but when the user explicitly supplies JCB/Sporttery data to ChatGPT analysis it may be used as auxiliary context only. If this is not the desired current rule, revise it explicitly.
