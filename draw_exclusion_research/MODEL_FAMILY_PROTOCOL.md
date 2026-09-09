# Draw-Exclusion Model-Family Research Protocol

Status: RESEARCH / VALIDATION SUPPORT
Formal execution source remains `draw_exclusion/latest.json` -> referenced daily file.

## Site-side model-family distinction

竞彩 and 北单（北京单场） draw-exclusion labels must be stored as different teacher/model families.

Canonical research identifiers:
- `JC_DRAW_MODEL`
- `BD_DRAW_MODEL`

Every prospective label record should preserve:
- `source_market`
- `teacher_model_family`
- `teacher_label`
- fixture identity / Titan match_id when safely matched
- source snapshot time
- pre-match freeze time
- post-match result later, without backfilling features

## Do not pool by default

Do not merge JC and BD labels into one calibration sample without explicitly testing model-family equivalence.

## Current hypotheses — NOT FACT

Possible working hypothesis:
- JC draw model may use more JC-specific official price structures;
- BD draw model may rely more on external-market 1X2/AH/OU structures.

This is not established and must not be hard-coded into MODEL_1. Validate from data.

## Execution-layer relationship

During the current one-month forward test beginning 2026-09-09:
- a verified `EXCLUDED=1` label from the authoritative current execution feed is a hard draw-removal constraint;
- `NOT_EXCLUDED=0` triggers enhanced draw audit, not a draw prediction;
- UNKNOWN/missing remains UNKNOWN.

The research family tag does not override the current execution-label contract.

## Prospective validation

For each family separately measure:
- excluded sample N;
- actual draw rate among excluded labels;
- false-exclusion rate;
- NOT_EXCLUDED draw rate;
- league / AH / 1X2 bucket stability;
- favourite-win vs underdog-win split after exclusion;
- interaction with underdog-outright company divergence.

Keep actual results separate from pre-match teacher labels so no result leakage enters the forward sample.
