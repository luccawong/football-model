# MODEL_1 Stage14 Forward Comparison

Effective from the Bayesian posterior score-engine repair onward.

## Cohorts

- Historical cohort: keep every previously frozen manually ranked correct-score Top1/Top3 unchanged.
- Intermediate research cohort: preserve already-created `AUTO_QUANT_MARKET_RECONSTRUCTION` samples exactly as frozen; do not relabel them posterior.
- Formal new cohort: use `BAYESIAN_POSTERIOR_POISSON_DIXON_COLES` only when a valid independent prior and the formal posterior packet exist.
- Do not backfill or recompute historical Top3 after results are known.

## Labels

Each score record must retain its origin:

- `MANUAL_PRE_PATCH`
- `AUTO_QUANT_MARKET_RECONSTRUCTION`
- `BAYESIAN_POSTERIOR_POISSON_DIXON_COLES`

`MARKET_RECONSTRUCTION` must never be renamed or reported as a Bayesian posterior.

## Formal Stage14 semantics

1. Build the independent log-rate prior from league/team information under `config/model_1_score_policy.json`.
2. Reconstruct market lambda observations from Pinnacle, Bet365 and Macau when valid.
3. Treat those bookmakers as one correlated market cluster; do not multiply them as three independent votes and do not use a simple average as the final lambda.
4. Apply only validated quantitative context updates. Narrative lineup/off-field claims cannot be converted into lambda shifts without a calibrated observation model.
5. Use anti-double-counting through `absorbed_fraction` / effective precision.
6. Integrate the posterior uncertainty through deterministic Monte Carlo into a Poisson/Dixon-Coles posterior-predictive score grid.
7. Preserve raw posterior draw mass even when the external website marks the match `EXCLUDED`; the execution-consistent Top3 may filter the displayed scores after the raw posterior is frozen.
8. 1X2 and formal AH direction are hard scoreline-consistency gates. OU is auxiliary for score selection under the current one-month ticket test and cannot issue or flip the formal main ticket.
9. If the prior is missing, output `MISSING/BAYESIAN_PRIOR_REQUIRED`; never silently fall back to a market-only formal score.

## Display contract

The final user-facing order is:

1. Formal main ticket, grade and execution price.
2. Immediately below it: frozen Stage14 Top1 / Top2 / Top3 with posterior probabilities and provenance.
3. Then the full SOP explanation and Red Team reasoning.

If Stage14 is unavailable, display `比分冻结：MISSING` with the reason instead of fabricating scores.

## Metrics

Track separately by cohort:

1. Top1 exact-score hit rate.
2. Top3 any-score hit rate.
3. Correct-score negative log likelihood when the full posterior grid is preserved.
4. Ranked Probability Score.
5. 1X2 Brier score derived from the score grid.
6. O/U log-loss / calibration across supported thresholds.
7. AH cover calibration.
8. Number of eligible matches, missing-prior matches and missing-market-reconstruction matches.
9. League and favourite-depth splits after sample size is adequate.

## Integrity

- Freeze predictions before kickoff.
- Preserve the source Titan match id and crawler snapshot.
- Preserve the prior calibration reference and market-company reconstruction provenance.
- Missing inputs remain `MISSING`.
- Stage14 does not automatically alter the formal main ticket.
- Compare cohorts prospectively; do not select only successful matches.
