# MODEL_1 Stage14 Bayesian Score Engine

This document records the user-approved formal correct-score architecture restored on 2026-09-11.

## Formal chain

League/team prior in log-rate space
→ validated context evidence
→ correlated Pinnacle/Bet365/Macau market-lambda cluster
→ Bayesian posterior over log(lambda_home), log(lambda_away)
→ posterior-predictive Poisson/Dixon-Coles score matrix
→ 1X2/AH hard consistency gate
→ OU auxiliary consistency preference
→ frozen Top1 / Top2 / Top3.

## Prior

The formal prior follows the 2026-09-04 score-model specification:

- log lambda_H = mu_league + HFA_league + Attack_H - Defense_A + X_beta_home
- log lambda_A = mu_league + Attack_A - Defense_H + X_beta_away

The prior must carry a calibrated 2x2 covariance matrix. Missing calibration is not replaced with invented certainty.

## Market lambda fusion

Pinnacle, Bet365 and Macau are not independent votes. MODEL_1 groups their valid market reconstructions into one correlated market likelihood in log-rate space. Cross-company disagreement increases uncertainty. The books keep their qualitative roles but do not receive arbitrary fixed percentage weights.

Market reconstruction is evidence, not the final score model.

## Bayesian update and anti-double-counting

Only validated quantitative context observations can move the lambda posterior numerically. Every update must declare a source group and may carry an absorbed_fraction; effective precision is reduced by 1 - absorbed_fraction when the same information is already reflected elsewhere.

Narrative claims, rumours or lineup descriptions without a calibrated mapping cannot be converted to numeric lambda shifts inside Stage14.

## Posterior predictive

MODEL_1 integrates over posterior lambda uncertainty using deterministic Monte Carlo and averages Dixon-Coles score grids. This is deliberately different from plugging a single posterior mean lambda into one Poisson grid.

Bivariate Poisson remains disabled until its shared component is historically trained and validated.

## Direction and OU

- The raw posterior matrix always preserves draw probability.
- The external draw-exclusion label does not rewrite the posterior.
- Final displayed Top3 may be filtered to the execution-consistent winner/AH path after the raw posterior is frozen.
- Under the current one-month test, OU is auxiliary for score selection and cannot create or flip the formal ticket.

## User-facing output order

Every future fully analysed match should display:

1. Formal main ticket + grade + execution price + one-line core logic.
2. Immediately below: `比分冻结` with Stage14 Top1 / Top2 / Top3, posterior probabilities and provenance.
3. Full SOP explanation.
4. Independent Red Team audit.

If the Bayesian prior or formal Stage14 packet is unavailable, write `比分冻结：MISSING` and name the missing input. Do not substitute market-only scores.
