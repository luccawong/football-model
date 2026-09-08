# GPT Football Analysis SOP — Full Stack v1.1

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
12. Independent totals: Macau/Pinnacle/Bet365 dynamic structure + OU ladder latent mean + WH/Lad Base-2.5; JCB auxiliary only when supplied.
13. Cross-market coherence: linked structure, not three independent votes.
14. Market attraction + favourite-failure paths.
15. Defensive / Lead-Lag / Attraction-Adjusted Divergence Stack:
    - keep ordinary company disagreement as the level-1 summary;
    - compare only de-vigged probabilities from the same time slice;
    - measure target-side defensive divergence in percentage points;
    - separate HOME / DRAW / AWAY and FAVORITE_NONWIN, never equate weak-side protection with weak-side outright win;
    - record persistence, independent feed clusters, lead-lag, copied-feed risk and cross-market confirmation;
    - UDS (Unnatural Defensive Signal) requires a low-attraction target that is nevertheless persistently protected by at least two independent clusters;
    - information grade A/B/C/NOISE is a signal-quality label only, not a ticket grade or probability adjustment;
    - all fields must be frozen pre-match. Post-result reconstruction is forbidden.
16. Draw Exclusion: default KEEP; exclusion needs hard evidence and score-distribution support.
17. Context extensions when fresh: weather/pitch, referee, ownership/agent/transfer network, club reciprocity, motivation.
18. Advanced event layer when available: xT/VAEP, set pieces, goalkeeper, pressing/possession; otherwise MISSING.
19. Correct-score layer: joint distribution and final Top3 direction-consistency gate.
20. Uncertainty audit: model/company disagreement, OOD/missingness, stale/conflicting sources.
21. Freeze H1.
22. Independent strongest coherent Red Team H2.
23. CONFIRM/DOWNGRADE/OVERTURN.
24. Formal main or unique non-main/PASS under standing execution rules.

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
Once a formal actionable ticket is issued it is locked. Later changes are explicit corrections.
