# Underdog Outright Historical Research Protocol

Status: RESEARCH_ONLY_UNCALIBRATED
Formal MODEL_1 ticket impact: NONE until explicitly promoted after validation.

## Objective

Identify whether abnormal bookmaker protection/divergence on the weak-side outright result produces stable prospective lift over matched historical baselines. Do not treat low absolute underdog probability as disqualifying; the target is abnormal relative pricing.

## Core sample

Primary target: matches where the favourite AH is -0.75 or deeper.

Stratify at minimum:
- -0.75
- -1.00
- -1.25
- -1.50
- -1.75
- -2.00 and deeper

Also split home-favourite vs away-favourite and league/competition where sample permits.

## Four outcome paths

For each bucket preserve:
1. favourite covers;
2. favourite wins but does not cover;
3. draw;
4. underdog wins outright.

Do not collapse (2), (3), and (4) into one generic favourite-failure label for research.

## Bookmakers

Primary set:
- William Hill
- Ladbrokes
- Bet365
- Pinnacle
- Interwetten
- Macau
- HKJC

For each available company preserve real opening and closing/current 1X2 odds and de-vig H/D/A probabilities.

## Residuals and divergence

For each match:
- Opening Market Median underdog-win probability
- Closing Market Median underdog-win probability
- Company Opening Residual = company opening underdog probability - opening median
- Company Closing Residual = company closing underdog probability - closing median
- Divergence Change = Closing Residual - Opening Residual

Historical normal bias:
- estimate company normal residual by league x AH bucket where sample permits;
- back off to AH bucket, then full sample when necessary;
- record the baseline level actually used.

Abnormal Residual = match residual - historical normal residual.

Do not call a static pairwise gap an upset signal until the normal pairwise gap for that match class is known.

## Structural vs dynamic-proxy divergence

Historical Titan databases may contain only opening and closing/final prices.

In that case:
- Structural Divergence = opening difference;
- Closing Divergence = final difference;
- Divergence Expansion = closing difference - opening difference.

Do NOT infer:
- who moved first;
- persistence duration;
- intraday reversal;
- lead-lag;
- money-flow timing.

Those require saved time-axis crawler samples.

## AH x 1X2 structures to test

A. AH deepens + underdog outright probability falls.
B. AH deepens + underdog outright probability stays roughly stable.
C. AH deepens + underdog outright probability rises.
D. AH retreats + underdog outright probability rises.
E. Favourite win tail strengthens + underdog win tail strengthens + draw compresses.
F. One company protects the weak side in both AH and 1X2.
G. Two or more independent company clusters protect the weak side.

Measure outright-win lift against matched baseline, not raw hit rate alone.

## Company combinations

Evaluate at least:
- Macau + Interwetten
- Macau + William Hill
- Macau + Ladbrokes
- William Hill + Ladbrokes
- Pinnacle + Bet365
- Macau + William Hill + Interwetten
- any >=2 independent companies
- any >=3 independent companies

Report N, underdog wins, hit rate, baseline, absolute lift, relative lift, odds ratio and confidence interval where feasible.

## Attraction control

Store an underdog attraction field when possible:
- LOW
- MEDIUM
- HIGH

If real betting-flow data are unavailable, use clearly labelled attraction proxies only; never claim a proxy is actual public money.

## Train / validation discipline

Prefer chronological split, e.g. older seasons for discovery and later seasons for validation.

Candidate thresholds may be discovered on training data only. Once frozen, test unchanged on validation data.

Do not tune on the validation set and then call the result out-of-sample.

## Macau structural-break research

Compare:
- <= 2026-08-31: Old/Control Regime
- >= 2026-09-01: Candidate New Regime

Track:
- Opening Residual
- Closing Residual
- Divergence Change
- Macau-Pinnacle
- Macau-WH
- Macau-Interwetten
- AH/1X2 coherence
- underdog outright outcomes

The 'regime change' remains a hypothesis until adequate matched evidence supports it.

## Betfair boundary

Betfair/OddsPapi remains SHADOW_ONLY and must not be blended into the bookmaker residual model during this research phase.

## Promotion rule

A candidate underdog-out-right rule becomes eligible for formal MODEL_1/next-model authority only after stable walk-forward evidence. Until then U0/U1/U2/U3 is descriptive evidence quality, not an automatic probability adjustment or ticket override.
