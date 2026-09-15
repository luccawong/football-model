# MODEL_1 Team Goal Baseline Integration

## Scope

This is an audit-only research layer: historical Titan team-goal baseline plus market-deviation context. It is not a new historical Bayesian prior and does not change MODEL_1 fixed weights, `mean_log_lambda`, covariance, Top3 ranking, AH hard gates, OU semantics, or the domestic prior activation state.

`formal_model_1_weight_impact` is always `NONE`. The existing domestic route remains `MARKET_ONLY_FORMAL`; the active European historical route remains `HISTORICAL_BAYESIAN`.

## Baseline

For a fixture strictly after the available history:

`lambda_home = league_home_goal_baseline × home_home_attack_strength × away_away_concede_factor`

`lambda_away = league_away_goal_baseline × away_away_attack_strength × home_home_concede_factor`

Four candidates are evaluated: five-year mean, recent two seasons, 365-day half-life time decay, and current season plus a ten-match historical-equivalent shrinkage. Selection is frozen from Train 2022-23 and 2023-24 only; 2024-25 is Validation and 2025-26 is Test. All five domestic leagues selected `time_decay`.

The Titan source is the completed-result SQLite with SHA-256 `cb409b3ceb882491671c08abbf6815fdfbaa398010de0377ad1d7bcf0d1531a7`. No odds, JCB, Betfair, current market or post-result field enters baseline fitting.

## Runtime packet

`gpt.team_goal_baseline.build_team_goal_baseline_packet(...)` returns the selected historical λ, total and margin, attack/concession factors, league baselines, sample sizes, fallback class, source hash and `no_future_leakage=true`. A historical fixture uses its precomputed strict-kickoff backtest snapshot when `match_id` is supplied. A past kickoff without a strict snapshot returns `MISSING`; it never falls back to the database end state.

`gpt.model_1_packet_bridge.build_production_correct_score_evidence(...)` attaches `team_goal_baseline_audit` after Stage14 is calculated. Missing baseline or calibration is non-blocking and cannot change the formal score packet.

## Market deviation

After the historical packet is built, Titan 1X2+OU reconstruction is compared with the historical λ:

- `market_home_lambda_residual = market λH − history λH`
- `market_away_lambda_residual = market λA − history λA`
- `market_total_residual = market total − history total`
- `market_goal_residual = market margin − history margin`

Train-only, league-specific Pinnacle/Bet365/Macau closing log-rate cluster residuals provide median, MAD, robust SD and percentiles. Interpretation labels such as `HOME_ATTACK_MARKUP`, `TOTAL_DISCOUNT` and `HOME_MARGIN_MARKUP` are diagnostics only. Positive residual never implies an automatic bet.

## Independence and future work

`independent_from_domestic_prior=true` and `overlap_scope=RESULT_HISTORY` are explicit. The layer must not be entered as a second Bayesian prior alongside Domestic Prior V2. Any future promotion requires incremental, correlation-aware, season-forward OOS validation and an explicit model-version decision.
