# MODEL_1 Stage14 Pre-match Context

Version: `MODEL_1-PREMATCH-CONTEXT-1.0.0`

This layer is an audit and evidence adapter around the existing Stage14 score
engine. It accepts four pre-match groups—`RECENT_FORM`, `LINEUP`,
`PLAYER_STATE`, and `SCHEDULE`—and validates timestamps, source provenance,
covariance and leakage fields before an update can reach either formal score
path.

`MARKET_ONLY_FORMAL` and `HISTORICAL_BAYESIAN` use the same validated update
contract. A quantified observation performs a normal log-rate Bayesian update
only after an approved calibration reference, status and version are present;
`TEST_ONLY` calibration requires explicit test permission. An
`UNCERTAINTY_ONLY` observation leaves the mean unchanged and adds only a
positive-semidefinite covariance inflation. Historical overlap and market
absorption reduce the effective fraction as
`(1 - absorbed_fraction) * (1 - historical_overlap_fraction)`.

Every supplied observation is cut at `context_snapshot_timestamp`, which must
be no later than kickoff and no earlier than its `evidence_timestamp`.
`market_snapshot_timestamp` is separate: it records whether the market could
already have absorbed the evidence. Evidence newer than the market snapshot but
older than the context snapshot is allowed and is marked
`market_context_time_mismatch=true`.

The current Titan archive is a result-only dataset. It has no production-
calibrated lineup, player-state, schedule or recent-form effect estimates.
Consequently the real-data builder returns `INSUFFICIENT_DATA` for omitted
groups and keeps formal λ unchanged. Caller-supplied quantified observations
must include a calibration reference and pass the strict pre-kickoff validator;
synthetic smoke coverage demonstrates this path without claiming real-data
accuracy.

The context layer cannot add bookmaker groups (`1X2`, `AH`, `OU_MAIN`,
`OU_CURVE`) and does not convert narrative claims into numeric shifts. Team Goal
Baseline remains research-only audit with
`formal_model_1_weight_impact=NONE`. Domestic Prior V2, Big5 SHADOW, UCL ACTIVE,
Stage14 weights, Top3, AH hard gates and OU logic are unchanged when context is
absent.

Run the real/synthetic smoke with:

```text
python scripts/build_stage14_prematch_context_smoke.py
```

The artifact is written to
`validation/stage14_prematch_context_smoke.json`.
