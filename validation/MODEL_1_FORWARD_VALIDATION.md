# MODEL_1 Prospective Forward-Validation Protocol

Status: ACTIVE_VALIDATION_SUPPORT
Formal betting authority: none; this document governs measurement, not picks.

## Model identity

- Default formal model: `MODEL_1`.
- Do not rewrite historical MODEL_1 rules or past traces after results.
- If MODEL_1 later underperforms expectations, freeze it and create MODEL_2 rather than mutating historical MODEL_1 identity.

## Evaluation horizon

Prefer an adequate prospective block before structural rebuild. A practical first review window is roughly 30-50 comparable fully analysed matches unless a hard data-integrity or logic bug is discovered earlier.

Do not modify the core after a few wins or losses merely to fit recent outcomes.

## Candidate provenance

Every validation record should store one of:
- QUICK_SCAN
- DEEP_ANALYSIS
- MANUAL

Also preserve candidate selection time so later analysis can detect selection bias.

## Intended fixed market sampling nodes

Where the collection pipeline supports them, preserve:
- T-5h
- T-2h
- T-1h
- T-30m
- T-10m

For each target:
- record expected nodes;
- record completed nodes;
- record missing nodes;
- record actual-vs-target collection-time deviation;
- do not interpolate or reconstruct a missing node from Opening/Current;
- store a separate collection-quality state such as HIGH/MEDIUM/LOW/INVALID.

Sampling quality must not itself be mistaken for a result-direction signal.

## Pre-match freeze

Before kickoff freeze:
- model_id / model_version;
- policy version;
- 18-stage formal trace;
- H1;
- Red Team H2 and verdict;
- final formal main ticket;
- ticket line, grade and actionable price;
- draw-exclusion label and model family when available;
- underdog U-grade where triggered;
- Top1/Top2/Top3 score ranking exactly as published;
- missing/conflict/QC states;
- Shadow research outputs separately.

No post-result feature reconstruction is allowed.

## Result confirmation

Do not infer completion from elapsed time alone.

Normal settlement only after a confirmed terminal status such as:
- FT
- AET
- PEN
- FINISHED
- MATCH_FINISHED

Abnormal statuses such as:
- POSTPONED
- CANCELLED
- ABANDONED
- INTERRUPTED
- DELAYED

remain outside normal settlement handling.

Otherwise keep `RESULT_PENDING_CONFIRMATION`.

## Objective ticket settlement

Keep two different fields:
- `direction_correct`
- `ticket_settlement`

Asian handicap and OU quarter-line settlement states:
- FULL_WIN
- HALF_WIN
- PUSH
- HALF_LOSS
- FULL_LOSS

Never collapse direction correctness and financial settlement into one label.

## Correct-score settlement

Preserve only pre-match frozen candidates and their order.

Track separately:
- Top1 exact hit;
- Top3 any hit;
- actual final score;
- formal handicap-direction settlement;
- optional conditional diagnostics such as `P(score hit | handicap direction hit)` once sample size is adequate.

Do not invent unrecovered Top2/Top3 candidates after the result and do not re-rank candidates post-match.

## Formal vs user execution

Primary model metric: formal main ticket correctness/settlement.

Separate fields may store:
- user actually bet: yes/no;
- executed price;
- stake;
- realised P&L.

The user not betting a formal ticket does not remove it from model-accuracy statistics.

## Post-match diagnostic layer

Before changing the model after a failure, classify likely cause:
- model logic;
- missing/late data;
- selection bias;
- time-axis interpretation;
- lineup error;
- market anomaly;
- off-field miss;
- execution-price issue;
- other documented cause.

A favourite -0.5 or deeper failure requires dedicated favourite-failure/upset review.

## Shadow / incremental-layer effect labels

`HELPFUL` / `HARMFUL` may be assigned only when:
- the alternative/shadow layer had an explicit pre-match frozen action or change recommendation;
- the relevant market result is confirmed and objectively settled.

Do not label `KEEP`, `UNRESOLVED`, missing-data, or non-action states as HELPFUL/HARMFUL after seeing the result.

This prevents post-match narrative relabeling.

## Betfair Shadow comparison

On the same selected sample preserve Baseline and Exchange Shadow separately.

Track:
- Baseline result;
- theoretical Shadow action;
- error corrected;
- error introduced;
- direction flip;
- grade change;
- `Net Corrections = corrected errors - introduced errors`.

Exchange Shadow cannot alter formal MODEL_1 statistics during the current test.
