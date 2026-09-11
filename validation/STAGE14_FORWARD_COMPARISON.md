# MODEL_1 Stage14 Forward Comparison

Effective from this patch onward.

## Cohorts

- Historical cohort: keep every previously frozen manually ranked correct-score Top1/Top3 unchanged.
- New cohort: generate Stage14 Top3 from the repository Quant reconstruction when a valid core-company reconstruction is available.
- Do not backfill or recompute historical Top3 after results are known.

## Labels

Each new score record must retain its origin:

- `MANUAL_PRE_PATCH`
- `AUTO_QUANT_MARKET_RECONSTRUCTION`
- `BAYESIAN_POSTERIOR` only when a separately validated posterior exists.

`MARKET_RECONSTRUCTION` must never be renamed or reported as a Bayesian posterior.

## Metrics

Track separately by cohort:

1. Top1 exact-score hit rate.
2. Top3 any-score hit rate.
3. Number of eligible matches and missing-quant matches.
4. Ranked probability / log-loss metrics when full probabilities are preserved.
5. League and favourite-depth splits after sample size is adequate.

## Integrity

- Freeze predictions before kickoff.
- Preserve the source Titan match id and crawler snapshot.
- Missing reconstruction remains `MISSING`.
- Stage14 research output does not automatically alter the formal main ticket.
- Compare cohorts prospectively; do not select only successful matches.
