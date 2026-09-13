# MODEL_1 Formal Extension — Post-Europe Market Residual Effect

Status: `ACTIVE_FORMAL_EXTENSION`
Effective date: 2026-09-13
Authorization: explicit user instruction to proceed with formal GitHub integration after V3.2 secondary audit PASS.
Freeze interaction: targeted override only. The MODEL_1 global freeze remains active for all other semantics.

## Formal feature

- Research name: `POST_EUROPE_MARKET_RESIDUAL_EFFECT`
- Runtime/interface field: `post_europe_residual_flag`
- Layer: fundamentals / schedule context
- Formal authority: ACTIVE contextual risk feature
- Fixed numeric weight: NONE

## Definition

For a team in a Big-Five domestic league match, set the feature to eligible/active only when all of the following are verified from pre-match-known schedule data:

1. The domestic competition is Premier League, La Liga, Serie A, Bundesliga or Ligue 1.
2. The team previously played UCL, UEL or UECL.
3. The current domestic match is the team's **first Big-Five league match after that European match**.
4. `0 < domestic_kickoff - europe_kickoff <= 168 hours`.
5. Match identity and timestamps are reliable enough to establish the sequence without inference from future results.

State semantics:
- `1` / ACTIVE: all conditions above are verified.
- `0`: verified not to meet the exposure definition.
- `UNKNOWN`: required schedule/identity evidence is missing or ambiguous.
- `NOT_CALIBRATED`: competition is outside the validated Big-Five scope.

Do not coerce UNKNOWN or NOT_CALIBRATED to 0.

## Evidence supporting admission

Canonical 2021–2026 study:
- post-Europe N = 1,833;
- control N = 8,672;
- 59 European-participating clubs;
- adjusted non-win effect = `+0.0410`;
- two-way cluster by team + domestic match: `p=0.0001`, CI `(0.0205, 0.0615)`;
- within-team GEE logit OR = `1.204`, `p=0.0004`;
- wild-cluster bootstrap `p<0.0001`;
- season adjusted sign consistency = `4/5` positive;
- league adjusted sign consistency = `5/5` positive;
- PPG residual = `-0.0715` points/match, `p=0.0014`;
- PPG residual is negative in `5/5` seasons and `5/5` leagues.

Canonical evidence package:
`research/post_europe_residual/`

## Runtime interpretation

This feature is evidence of a **residual negative performance bias after opening-market pricing**, not proof of a single causal mechanism such as fatigue.

The historical `+4.1pp` non-win estimate and `-0.0715` PPG residual are calibration evidence only. They are **not** authorized as fixed per-match probability, goal, grade or handicap adjustments.

The feature must enter the reasoning chain as a validated schedule-risk prior/context feature and be reconciled with the specific match's:
- opponent strength;
- home/away status;
- exact rest interval;
- prior European game importance and game state;
- next-fixture priority when pre-match known;
- available rotation/lineup evidence;
- current 1X2/AH/OU market structure.

If both teams are ACTIVE, do not blindly apply equal fixed penalties to both sides. Treat the bilateral exposure as relative context and avoid double counting.

## Stage discipline

- Record/evaluate the feature in Stage 1 Fundamentals under schedule/priority pressure.
- Stage 3 Opening First Impression remains **opening-structure-only** and must not be contaminated by this contextual feature.
- Integrate the feature only when fundamentals/context are later reconciled with 1X2, AH, OU, favourite-failure paths and Red Team review.
- The feature may downgrade confidence in an otherwise marginal favourite path or strengthen a failure-path hypothesis, but it cannot mechanically force a ticket.

## Non-promoted interactions from this research

The following are **not** separate formal MODEL_1 weights from this study:
- shallow-favourite AH depth effect: `WATCH` only (matched +3.8pp, p=0.253);
- TRUE_RETREAT × post-Europe: `UNRESOLVED / INSUFFICIENT_CONTROL_SAMPLE`;
- Europe-away × league-away: REJECT as a standalone interaction;
- UECL sandwich: REJECT as a standalone interaction;
- rest bucket: REJECT as a standalone interaction;
- XI carryover / rotation class: NOT VALIDATED because historical lineup data are unavailable.

Existing independently validated market signals, including TRUE_RETREAT where otherwise authorized, retain their own status; this extension does not duplicate or re-weight them.

## Methodological boundary

The study estimates a market-residual association after controlling opening-market strength and team/context covariates. Do not rewrite it as a universal causal statement that European competition itself mechanically causes a fixed deterioration.

## Change control

This extension is the only 2026-09-13 targeted MODEL_1 semantic override authorized by the user's instruction to proceed after V3.2 PASS. It does not end the one-month MODEL_1 freeze and does not authorize unrelated threshold, weight, stage-order, source-authority or ticket-policy changes.
