# GPT Football Analysis SOP — Full Stack v1.3

1. Market snapshot + Data Gate: state, timestamp, identity, MAIN/ALT, freshness, conflicts, missing core timelines.
2. Opening-only first impression: no later results/injuries/movements contaminate opening interpretation.
3. Opening validity/lifecycle: true opening vs information re-opening vs ordinary movement.
4. Off-field/source scan: official club/league first, then major media/beat reporting; label rumours.
5. Independent strength prior: league baseline/HFA + fresh rating/xG/fundamental evidence with anti-double-counting.
6. Squad/tactical: official/predicted XI distinction, injuries/suspensions, expected-minutes relevance, formation/matchup.
7. Schedule/Priority: past rest plus future 7–10 days, rotation/travel; no arbitrary probability penalty.
8. Quant Packet freeze: de-vig, company pp divergence, market-implied lambda, Dixon-Coles, AH/OU settlement, score grid.
9. Feature Packet freeze: reversals/failed upgrades, freshness, disagreement, entropy/uncertainty, module gates.
10. 1X2 pricing: WH/Lad primary pair; Interwetten cold-side; Pinnacle anchor; Macau signal; Bet365 comparator; same-time slices.
11. Asian handicap: line+water lifecycle, failed upgrade/downgrade, adjacent counterfactual lines.
12. Independent totals: Macau/Pinnacle/Bet365 dynamic structure + OU ladder latent mean + WH/Lad Base-2.5; JCB auxiliary only when explicitly supplied as external analysis context.
13. Cross-market coherence: linked structure, not three independent votes.
14. Market attraction + favourite-failure paths.
15. Mandatory Underdog Outright Audit for favourite handicap deeper than -0.5 (i.e. -0.75 and beyond):
    - begin from an independent fundamental baseline; low absolute underdog win probability is normal and is not itself evidence against an upset;
    - compare WH, Ladbrokes, Bet365, Pinnacle, Interwetten, Macau and HKJC weak-side outright 1X2 prices after de-vigging;
    - compare closest same-time slices; separate structural opening divergence from later divergence expansion;
    - measure company residual versus the same-match company median and, where historical calibration exists, abnormal residual versus that company's normal handicap/league bias;
    - inspect whether AH deepens while weak-side outright probability refuses to fall or rises, whether AH retreats while weak-side outright probability rises, and whether favourite and underdog win tails strengthen while draw is compressed;
    - distinguish 'underdog covers' from 'underdog wins outright'; never convert +AH support into an outright-upset claim without 1X2 evidence;
    - assign U0/U1/U2/U3 as an outright-upset evidence grade based on cross-company divergence, lifecycle and AH confirmation, never on the underdog's absolute probability alone;
    - Red Team must explicitly ask whether the analysis is inventing reasons for the favourite while ignoring weak-side outright pricing evidence.
16. Defensive / Lead-Lag / Attraction-Adjusted Divergence Stack:
    - keep ordinary company disagreement as the level-1 summary;
    - compare only de-vigged probabilities from the same time slice;
    - measure target-side defensive divergence in percentage points;
    - separate HOME / DRAW / AWAY and FAVORITE_NONWIN, never equate weak-side protection with weak-side outright win;
    - record persistence, independent feed clusters, lead-lag, copied-feed risk and cross-market confirmation;
    - UDS (Unnatural Defensive Signal) requires a low-attraction target that is nevertheless persistently protected by at least two independent clusters;
    - information grade A/B/C/NOISE is a signal-quality label only, not a ticket grade or probability adjustment;
    - all fields must be frozen pre-match. Post-result reconstruction is forbidden.
17. External Draw-Exclusion Forward-Test Override — hard execution rule during the current one-month test beginning 2026-09-09:
    - authoritative source is `draw_exclusion/latest.json` -> the referenced `draw_exclusion/daily/YYYY-MM-DD.json`; do not substitute the legacy research label file;
    - `EXCLUDED=1`: treat draw exclusion as a hard execution constraint. Do not independently re-open or veto the website's draw decision during the test. Remove draw from the execution branch and analyze HOME WIN vs AWAY WIN, then favourite cover / favourite win-no-cover / underdog outright upset;
    - `NOT_EXCLUDED=0`: this does NOT predict a draw, but draw must remain an active path and receive an enhanced mandatory audit before any final ticket. Review WH/Lad draw position, all core-company de-vig draw probabilities, opening-to-current draw lifecycle, closest same-time-slice divergence, AH/1X2/OU consistency, score-grid draw mass and 0-0/1-1/2-2 compatibility where relevant;
    - for `NOT_EXCLUDED=0`, Red Team must explicitly test whether draw is the leading favourite-failure path and whether the proposed AH ticket survives that draw path. A deep favourite ticket cannot be justified only by high favourite win probability;
    - `NULL/UNKNOWN` or a match absent from the verified daily pool stays UNKNOWN; never coerce missing into NOT_EXCLUDED;
    - research records still preserve actual draw outcomes so the external website can be evaluated prospectively after results.
18. Context extensions when fresh: weather/pitch, referee, ownership/agent/transfer network, club reciprocity, motivation.
19. Advanced event layer when available: xT/VAEP, set pieces, goalkeeper, pressing/possession; otherwise MISSING.
20. Correct-score layer: joint distribution and final Top3 direction-consistency gate.
21. Uncertainty audit: model/company disagreement, OOD/missingness, stale/conflicting sources.
22. Freeze H1.
23. Independent strongest coherent Red Team H2.
24. CONFIRM/DOWNGRADE/UPGRADE/OVERTURN.
25. Final output: exactly ONE formal main ticket per fully analysed match. Non-main tickets are abolished. Final PASS is not allowed under the current ticket policy; uncertainty must be expressed through grade and execution conditions instead.

## Canonical memory reference

Runtime should load `gpt/FOOTBALL_CANONICAL_MEMORY.md` and `config/active_decision_policy.json` before applying lower-level modules. If a lower-level rule conflicts with the newest explicit policy, flag and update the repository rather than silently executing the older rule.

## Divergence validation protocol

The Defensive Divergence Stack is `RESEARCH_ONLY_UNCALIBRATED` until prospective validation is adequate. Store the full pre-match snapshot first, then settle outcomes later. At minimum validate by league/market/handicap bucket:

- target-side divergence magnitude (pp);
- attraction score and low-attraction subset;
- persistence duration;
- independent cluster count versus copied-feed clusters;
- lead-lag and whether mainstream books subsequently followed;
- cross-market confirmation;
- football path split: favourite win / draw / underdog win / favourite non-win.

Do not select companies or thresholds after seeing results. Do not promote information grade into probability or ticket weight until walk-forward evidence supports it.

## Validation
Use chronological walk-forward Brier/RPS/log-loss/reliability. Do not change core logic from a few outcomes. Prefer league-specific calibration; Chinese football stays separate for research/calibration. Black-box ML, Kelly and live-inplay Bayesian remain RESEARCH_ONLY until promoted after validation.

## Ticket lock
Once a formal actionable ticket is issued it is locked. Later changes are explicit corrections with old -> new; silent replacement is forbidden.
