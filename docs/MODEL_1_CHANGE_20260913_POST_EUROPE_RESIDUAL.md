# MODEL_1 Change Record — 2026-09-13 Post-Europe Residual Feature

Change type: targeted formal extension during global freeze
Authorization: explicit user instruction after V3.2 research PASS
Global freeze ended: NO

## Added

- formal feature `POST_EUROPE_MARKET_RESIDUAL_EFFECT`;
- interface field `post_europe_residual_flag`;
- formal overlay `models/MODEL_1_EXTENSION_20260913_POST_EUROPE_RESIDUAL.md`;
- policy `config/post_europe_residual_policy.json`;
- canonical evidence package `research/post_europe_residual/`;
- root portability files `AI_HANDOFF.md` and `CURRENT_STATE.md`.

## Formal semantics

The feature identifies the first Big-Five league match after UCL/UEL/UECL when the verified gap is greater than zero and no more than 168 hours. It is a validated contextual residual-risk feature.

No fixed +4.1pp non-win, -0.0715 PPG, grade, goal or AH adjustment is authorized. The estimates are research calibration evidence, not deterministic runtime weights.

The feature does not contaminate the opening-only first-impression stage and cannot mechanically force a ticket.

## Research gate

V3.2 final gate: 6/6 PASS.

Key robustness:
- two-way cluster coefficient +0.0410, p=0.0001;
- GEE OR 1.204, p=0.0004;
- wild cluster p<0.0001;
- 4/5 seasons positive adjusted effect;
- 5/5 leagues positive adjusted effect;
- PPG residual -0.0715 with 5/5 seasons and 5/5 leagues negative.

## Explicitly not promoted

- shallow-favourite AH interaction;
- post-Europe × TRUE_RETREAT incremental rule;
- Europe-away × league-away standalone effect;
- UECL-sandwich standalone effect;
- rest-bucket standalone effect;
- XI-carryover/rotation-class historical mechanism.
