# Football Cross-Chat Memory Gap Audit — 2026-09-09

Purpose: compare the active MODEL_1 GitHub rules against remembered football-model decisions from prior chats and preserved project artifacts. This document is an audit ledger: it separates rules that should enter MODEL_1, research/validation rules that must stay outside formal decision authority, and legacy/conflicting rules that must not silently override newer policy.

## A. Missing/under-specified rules promoted into current MODEL_1 documentation

### A1. Depth over batch size
- Deep analysis should be match-by-match. One match at a time is preferred; two is the practical maximum before depth risks compression.
- If more than two matches are supplied, do not compress the required modules merely to finish faster.
- Near kickoff use ticket-first delivery, but do not skip the internal SOP.

### A2. Opening rationality is a market-intent audit, not just a line-strength check
- Establish a reasonable opening band from fundamentals before judging the quoted opening.
- Ask why the bookmaker chose this opening rather than the adjacent alternative price/line.
- Consider blocking, inducement, attraction and risk-distribution explanations, but label them as inference rather than fact.
- A suspiciously high favourite price can itself increase underdog attraction; it is not automatically resistance against the favourite.
- Do not delete the draw path merely because the favourite opening looks intentionally high or low.

### A3. Price/value and direction are separate
- Do not reject a stable direction solely because theoretical EV/value is thin.
- Distinguish: (1) payout/EV changed but the result path is unchanged; (2) price movement contains new information that changes market structure/result path.
- Only type (2) is a core reason to correct direction.
- Long-run execution normally prefers decimal odds around 1.80 or better, but exact minimum is ticket-specific.

### A4. Missing timeline disclosure
- If WH, Ladbrokes, Pinnacle, Interwetten, Bet365, Macau/HKJC or another key company lacks a verifiable detailed timeline, explicitly disclose the company and match.
- Opening/current values are not a substitute for a real time axis.
- Blank Titan timeline regions may be source/interface/API failure; keep MISSING rather than inventing a path.

### A5. Quick scan and deep analysis are different products
- Quick scan is selection only; deep analysis must return to opening, lifecycle and the full MODEL_1 order.
- Quick scan target is roughly T-5h and uses only pre-match Tier-1 matches.
- Champions League/high-profile matches are not dropped merely because structure is unclear; retain a structure/direction grade for later selection.
- Quick-scan core bookmaker set remains HKJC, Macau, William Hill, Ladbrokes and Interwetten; Pinnacle/Bet365/Crown belong to deeper confirmation rather than the first scan sheet.

### A6. Same-day off-field hierarchy
- Latest official lineup/club/league announcement > same-day mainstream/beat reporting > earlier daily digest > unverified rumour.
- A later official contradiction overrides the earlier claim as current fact; the earlier item may remain only as an explanation for prior market movement.
- Do not force all off-field items to point in the same direction.

### A7. Model output and user's personal bet are separate
- Formal main ticket accuracy is the primary model metric even if the user does not personally bet that ticket.
- Actual execution price/stake/P&L are separate secondary fields.

## B. Validation/data-pipeline memories that should be preserved but not become betting signals

### B1. Fixed prospective sampling nodes
For formal shadow/validation collection where the pipeline supports it, preserve the intended checkpoints:
- T-5h
- T-2h
- T-1h
- T-30m
- T-10m

Rules:
- record actual completed vs expected nodes;
- record missing nodes and collection-time deviation;
- never interpolate or back-fill missing nodes from Opening/Current;
- keep quality state such as HIGH/MEDIUM/LOW/INVALID separate from the formal match direction.

### B2. Candidate-source provenance
Validation records should preserve how a match entered the sample:
- QUICK_SCAN
- DEEP_ANALYSIS
- MANUAL

Preserve candidate selection time so selection bias can be audited later.

### B3. Result confirmation and settlement
- Do not infer 'finished' merely from elapsed clock time.
- Only confirmed terminal statuses such as FT/AET/PEN/FINISHED/MATCH_FINISHED qualify for normal settlement.
- POSTPONED/CANCELLED/ABANDONED/INTERRUPTED/DELAYED are abnormal and excluded from normal settlement.
- Otherwise keep RESULT_PENDING_CONFIRMATION.
- 1X2/AH/OU settlement should be objective and separate from 'direction_correct'.
- Quarter-line settlement states: FULL_WIN / HALF_WIN / PUSH / HALF_LOSS / FULL_LOSS.

### B4. Raw/QC preservation
- Preserve raw aggregate/ambiguous records and conflict/QC flags.
- Clean analysis should prefer record-level MAIN history events where available.
- Source absence is `SOURCE_NO_DATA` / MISSING, not a fabricated value.
- Do not fuzzy-match ambiguous fixtures into a validated sample merely to increase coverage.

## C. Draw-exclusion research memories not yet fully represented

### C1. J竞彩 vs 北单 model-family separation
A site-side clarification states that 竞彩 draw-exclusion and 北单（北京单场） draw-exclusion use two different models.

Research requirement:
- preserve separate model families, never pool them blindly;
- recommended identifiers: `JC_DRAW_MODEL` and `BD_DRAW_MODEL`;
- record `source_market`, `teacher_model_family`, `teacher_label` on each prospective sample;
- the hypothesis that 北单 relies more heavily on external markets while 竞彩 relies more on 竞彩-specific structure is NOT established fact and must be tested, not hard-coded.

### C2. Current one-month execution override remains newer
Older research methodology kept external draw labels independent and did not allow them to delete draw directly. That rule is superseded at the execution layer for the one-month test beginning 2026-09-09:
- EXCLUDED=1 is a hard execution constraint;
- NOT_EXCLUDED=0 requires enhanced draw audit;
- actual results remain preserved for prospective validation.

## D. Underdog-out-right historical database research that belongs outside formal MODEL_1 weights until validated

Priority research stack:
1. Handicap-band four-path baselines: favourite cover / favourite win-no-cover / draw / underdog outright win.
2. Company-specific normal underdog residuals by league and AH band.
3. Opening divergence vs closing divergence and divergence expansion.
4. Company-pair and multi-company combinations.
5. Underdog Attraction Score / proxy.
6. AH x 1X2 structures such as AH deepening while underdog ML is protected.
7. Train/validation chronological split; never discover thresholds on the validation set.
8. Measure lift against matched baseline, not raw upset rate alone.
9. Macau pre/post 2026-09-01 structural-break comparison.
10. Betfair remains separate Shadow and must not be blended into the bookmaker-divergence model yet.

No exact pp threshold should become formal until adequate historical/walk-forward validation supports it.

## E. Model-stability memories

- More modules do not automatically improve the model; excessive decision authority can create decision instability.
- Freeze a model version over an adequate prospective sample before judging it; do not modify the core after a few wins/losses.
- A practical evaluation batch of roughly 30-50 comparable matches is preferred before structural rebuild unless a hard data/logic bug is discovered.
- If MODEL_1 is below expectations, freeze it and build MODEL_2 rather than rewriting MODEL_1 history.

### Betfair Shadow experiment
- Compare the same selected matches under Baseline and Shadow.
- Track errors corrected, errors introduced, direction flips and grade changes.
- `Net Corrections = corrected errors - introduced errors` is the key research diagnostic.
- Betfair remains SHADOW_ONLY until prospective evidence justifies a formal authority change.

## F. Historical/legacy integration conflicts — do NOT silently promote

### F1. Sporttery/JCB scope conflict
Two historical branches exist:
- older/current software-V2 production decisions disabled current Sporttery/JCB production output;
- ChatGPT match-analysis memories allow JCB/Sporttery as auxiliary context when explicitly supplied, never primary OU evidence.

Current safe interpretation for MODEL_1:
- no mandatory JCB/Sporttery dependency;
- no JCB/Sporttery production hard requirement;
- if explicitly supplied in a ChatGPT analysis, it may be shown only as auxiliary context and cannot override the primary external/Titan market analysis.

This remains a documented integration boundary rather than a reason to alter current picks.

### F2. Ordinary bookmaker provider vs match-analysis source
A software branch used API-Football for ordinary bookmaker pricing and OddsPapi only for Betfair Exchange, while the user's current chat workflow supplies Titan deep-crawler packets for match analysis.

Do not conflate these layers:
- Titan packet is the current user-supplied analysis packet when provided;
- OddsPapi is the genuine Betfair Exchange provider;
- software-provider architecture may use API-Football separately;
- a Titan row labelled Betfair is never equivalent to OddsPapi `betfair-ex`.

### F3. Legacy strategy identifiers
Historical software identifiers such as `football_v2.0-a5` must remain historically reproducible and must not be retroactively renamed MODEL_1. MODEL_1 is the new canonical model identity beginning 2026-09-09; legacy strategies remain frozen historical artifacts.

## G. Research memories intentionally not promoted to formal decision rules

- Macau post-2026-09-01 'operator/regime change' remains a hypothesis.
- Defensive/lead-lag/attraction-adjusted divergence thresholds remain uncalibrated research.
- JCB historical goal-count curves/0-goal/7+ anchors remain historical research, not primary current totals logic.
- Betfair microstructure heuristics remain Shadow.
- Black-box ML, Kelly staking and live in-play Bayesian remain research-only until explicitly promoted.

## H. Audit result

The largest gaps found after the first migration were not the central 18-stage SOP itself; they were the surrounding controls:
- prospective sampling cadence;
- result-confirmation/settlement rules;
- candidate provenance and selection-bias tracking;
- JC vs BD draw-model-family separation;
- model-stability / 30-50-match freeze discipline;
- provider/JCB legacy conflicts;
- underdog historical research protocol;
- one-match-at-a-time/depth-preservation interaction rule.

These items should be loaded as supporting contracts around MODEL_1, but only the ACTIVE items may affect the formal ticket.
