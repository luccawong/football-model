# MODEL_1 — 2026-09-12 Matchday Failure Audit

Status: RESEARCH_ONLY / ZERO_FORMAL_IMPACT  
Model: MODEL_1  
Audit date: 2026-09-13  
Scope: Beijing-date 2026-09-12 formal tickets already frozen before settlement.

This document is a technical diagnostic. It does not rewrite any pre-match ticket and does not modify frozen MODEL_1 semantics.

## 1. Severity

- Pre-2026-09-12 settled block: 12 formal tickets, 10 positive settlements = 83.33%.
- 2026-09-12 block: 14 formal tickets, 5 positive, 9 losses = 35.71%.
- Cumulative after the day: 26 settled, 15 positive = 57.69%.
- One matchday reduced cumulative positive rate by 25.64 percentage points.

This is treated as a matchday-level correlated failure, not an isolated losing streak.

## 2. Cross-match exposure concentration

All 14 formal tickets on 2026-09-12 were on the HOME side of their respective market (home favourite, home winner-only, or home underdog handicap). There were zero away-side formal tickets and zero OU formal tickets in this block.

Premier League subset:
- 6 MODEL_1 formal tickets.
- 6/6 were HOME-side exposures.
- 0/6 positive settlements.
- The seven EPL matches played that Saturday ended with 0 home wins: 4 draws + 3 away wins.

MODEL_1 currently has no formal matchday/portfolio exposure audit, so individually reasonable-looking tickets can accumulate into one highly correlated directional position.

## 3. Draw-exclusion concentration and failure

Of the 14 formal tickets:
- 12 had JC execution label EXCLUDED.
- 6 of those 12 finished as draws.
- Therefore the EXCLUDED pool produced only 6/12 actual non-draw outcomes on this day (50%).

The six actual draws inside EXCLUDED were:
- Chelsea 2-2 Hull City
- Bournemouth 2-2 Brentford
- Liverpool 0-0 Fulham
- Cologne 1-1 Werder Bremen
- Athletic Bilbao 1-1 Elche
- Tottenham 0-0 Everton

These six draw outcomes account for 6 of the day's 9 formal-ticket losses (66.7%).

Counterfactual exposure decomposition only (not a claim that an alternative model would have selected the remaining matches): if these six correlated draw-failure cases are removed from the diagnostic sample, the remaining day is 5 positive / 8 = 62.5%.

## 4. Current forward-sample draw-label diagnostic

Across all 26 settled formal tickets currently recorded:
- EXCLUDED: 17 tickets, 6 positive / 11 losses; 7 actual draws.
- NOT_EXCLUDED: 8 tickets, 8 positive / 0 losses; 0 actual draws.
- UNKNOWN: 1 ticket, positive; actual draw.

This sample is selected and confounded by match type, so it is not a causal estimate of the external site's quality. However, it is enough to say the EXCLUDED execution branch has not demonstrated positive calibration in the current MODEL_1 forward sample.

## 5. Winner-only branch

Five 2026-09-12 formal tickets were winner-only home selections under EXCLUDED:
- Hoffenheim win — WIN
- Crystal Palace win — LOSS
- Bournemouth win — LOSS
- Cologne win — LOSS
- Tottenham win — LOSS

Result: 1/5 positive = 20%.

Three B- tickets were Crystal Palace, Cologne and Tottenham. All three were EXCLUDED + home-side winner-only and all three lost. This does not establish a universal B- rule, but it shows that the combination `B- + EXCLUDED + winner-only + same-side day concentration` was a severe exposure amplifier.

## 6. Market/draw-path mismatch

Using the mean current de-vig draw probability from the archived Titan core 1X2 companies:
- EPL selected six: expected draw count from market probabilities ≈ 1.37; observed draws = 4.
- Illustrative independent Poisson-binomial tail P(draws >= 4) ≈ 2.63%.
- Twelve EXCLUDED tickets: expected draw count ≈ 2.72; observed draws = 6.
- Illustrative independent Poisson-binomial tail P(draws >= 6) ≈ 3.46%.

These are anomaly diagnostics only. Independence is not literally true across same-day matches and bookmaker prices are not calibrated MODEL_1 probabilities.

The important architecture issue is source dependence: if the external draw classifier is itself derived partly from market prices, combining `market says draw lower` + `external site says EXCLUDED` as two independent confirmations can double-count the same underlying information. Until source independence is established, the external label should be treated as a correlated execution input in research diagnostics.

## 7. Match-level failure classes

### High structural relevance

**Crystal Palace vs Ipswich**
- Formal: Crystal Palace win B-.
- Core 1X2 mean home probability fell about 5.38pp.
- Macau / Pinnacle / Bet365 AH all retreated materially toward Palace (roughly -0.5/-0.75 to -0.25).
- Final 2-3.
- Diagnosis: winner-only side selection remained home despite a broad anti-home repricing. Red Team challenge resistance was insufficient.

**Liverpool vs Fulham**
- Formal: Liverpool -1 B.
- Core home probability fell about 3.00pp.
- Pinnacle and Bet365 retreated from -1.25 to -1; Macau held -1.25 but moved Liverpool to high water.
- Short-turnaround freshness was a known pre-match negative.
- Final 0-0.
- Diagnosis: known schedule + AH retreat + draw-path risk were not strong enough to stop the ticket after EXCLUDED.

**Tottenham vs Everton**
- Formal: Tottenham win B-.
- Market repriced Tottenham modestly stronger, but the team entered with a major scoring drought.
- Final 0-0.
- Diagnosis: price reinforcement was allowed to dominate a highly relevant attacking-state counter-signal after draw removal.

**Chelsea vs Hull / Athletic Bilbao vs Elche**
- Both deep favourites received meaningful AH reinforcement.
- Both finished drawn.
- Diagnosis: `market reinforcement + EXCLUDED` created false confidence in a branch where draw still carried material market probability.

### Mixed / potentially variance-heavy

**Bournemouth vs Brentford**
- Formal: Bournemouth win.
- Final 2-2 despite strong Bournemouth chance/shot pressure.
- Diagnosis: draw-exclusion failure plus finishing/game-management variance; not clean evidence of wrong side model alone.

**Sunderland vs Arsenal**
- Formal: Sunderland +0.75 B+.
- Sunderland missed a penalty at 0-0; second Arsenal goal came in stoppage time after a red-card sequence.
- Diagnosis: underdog handicap thesis failed in settlement, but tail events materially widened the final margin. Lower structural weight than the draw-cluster failures.

**Mainz vs Frankfurt**
- Formal: Mainz -0.75 B.
- Strong market reinforcement toward Mainz, final 1-3.
- Diagnosis: favourite side-selection / market-reinforcement false positive; separate from the draw cluster.

## 8. Data-integrity fault found during audit

Two Titan IDs in the statistics workbook were incorrect:
- Chelsea vs Hull City: recorded 3003882; archived V23 source is 3003881.
- Crystal Palace vs Ipswich: recorded 3003880; archived V23 source is 3003883.

This is a post-recording QC fault unless further evidence shows the pre-match analysis queried the wrong match. It must be corrected because future joins by match_id can otherwise contaminate draw-label and crawler diagnostics.

## 9. Root-cause ranking

1. **VERY HIGH — Correlated execution failure:** hard EXCLUDED branch + draw cluster.
2. **VERY HIGH — Missing matchday exposure audit:** 14/14 home-side positions; EPL 6/6 home-side positions.
3. **HIGH — Winner-only branch fragility:** 1/5 on the day, especially B- cases.
4. **HIGH — Source-independence / double-count risk:** external draw label may not be independent from market information.
5. **MEDIUM-HIGH — Red Team challenge resistance:** Palace and Liverpool had material pre-match counter-signals but tickets survived.
6. **MEDIUM — Forced-ticket policy as exposure amplifier:** no-PASS means weak B- cases still become formal positions.
7. **REAL BUT SECONDARY — Match variance / late margin events:** relevant for Bournemouth and Sunderland, not sufficient to explain the day's collapse.

## 10. Research candidates for MODEL_2 / future explicit override

These are NOT active MODEL_1 rules during the freeze:

- Matchday Regime & Exposure Audit before final execution: count same-league/same-side/favourite/underdog/draw-label concentration.
- Label-saturation flag when a large majority of analysed matches share EXCLUDED.
- External-label source-independence test; do not count correlated signals as separate evidence.
- Winner-only safety research for `EXCLUDED + B-` and for market moves materially against the selected side.
- Independent draw-posterior floor research rather than treating an external EXCLUDED label as execution-equivalent to zero draw risk.
- Formal cross-match correlation logging, without mechanically reversing tickets.

MODEL_1 remains frozen unless the user explicitly overrides the freeze. Data/QC corrections and this research log are allowed under the current specification.
