# Codex Task: Five-League Team Goal Baseline 2021-2026

Read first:
- `research/team_goal_baseline/RESEARCH_PROTOCOL.md`
- `config/active_decision_policy.json`
- `config/model_1_supporting_contracts.json`

## Objective

Build a reproducible historical team scoring/conceding database for the Premier League, La Liga, Serie A, Bundesliga and Ligue 1 covering the completed seasons 2021-22 through 2025-26, plus 2026-27 YTD as a separately flagged partial season.

The final system must support a matchup lookup such as Team A vs Team B and return both raw average-goal differences and normalized attack-vs-defence matchup baselines.

## Data-source requirements

Use a stable public historical match-results source with match date, home team, away team, home goals and away goals. Preserve source URLs/identifiers and create a provenance table. Cross-check aggregate season totals against a second reliable source or official league table totals when feasible.

Do not silently merge conflicting records. Log discrepancies.

## Required implementation

Create:

- `scripts/build_team_goal_baseline.py`
- `scripts/query_team_goal_matchup.py`
- `data/team_goal_baseline/team_aliases.csv`
- `database/exports/team_goal_baseline/team_season_baselines.csv`
- `database/exports/team_goal_baseline/league_season_baselines.csv`
- `database/exports/team_goal_baseline/team_long_run_baselines.csv`
- `database/exports/team_goal_baseline/source_provenance.csv`
- `database/exports/team_goal_baseline/qc_report.csv`

If the repository convention suggests a better path, keep the same semantics and document the change.

## Required metrics

For each team-season calculate:
- matches
- GF_per_match
- GA_per_match
- home_GF_per_match
- home_GA_per_match
- away_GF_per_match
- away_GA_per_match
- total_goals_per_match
- goal_difference_per_match
- sample_size flags

For each league-season calculate:
- league_home_GF_per_match
- league_away_GF_per_match
- league_total_goals_per_match

Normalized metrics:
- home_attack_strength
- away_attack_strength
- home_defence_weakness
- away_defence_weakness

For home A vs away B calculate:
- raw_average_GF_gap
- normalized_attack_gap
- lambda_home_baseline
- lambda_away_baseline
- matchup_goal_gap
- matchup_total_baseline

Use the formulas in `research/team_goal_baseline/RESEARCH_PROTOCOL.md`.

## Recency variants

Build at least:
1. five-season unweighted;
2. two-season rolling;
3. recency-weighted multi-season;
4. current-season shrunk baseline;
5. venue-specific versions.

Do not choose one as formal MODEL_1 output by intuition. Produce an out-of-sample comparison table first.

## Time-safety

For historical validation, a match on date D may only use matches before D. No result leakage.

## Promotion/relegation

Do not directly mix lower-division scoring rates into top-flight rates. If lower-division translation is implemented, estimate it from promoted-team historical transitions and report the method separately. Otherwise shrink sparse promoted-team top-flight samples toward league mean.

## Validation outputs

Create a validation report comparing each candidate prior against a league-average baseline and the existing MODEL_1 score prior where callable. Include:
- home-goal Poisson deviance/log-likelihood
- away-goal Poisson deviance/log-likelihood
- total-goals MAE/RMSE
- goal-difference MAE/RMSE
- calibration by 0,1,2,3,4,5+ goals
- league-by-league and season-by-season performance

## QC

Fail loudly on:
- duplicate matches
- impossible scores
- missing canonical team mapping
- mixed competitions
- season/date mismatch
- partial-season rows accidentally treated as completed seasons
- future-data leakage

## Deliverable summary

At completion, write `research/team_goal_baseline/RESULTS.md` containing:
- data coverage
- sources
- QC results
- best-performing baseline variant by league
- whether the raw average-goal difference adds useful information after normalization
- recommendation: KEEP_SHADOW / PROMOTE_CANDIDATE / REJECT

Do not modify MODEL_1 formal coefficients or ticket thresholds in this task. Promotion requires explicit user approval after results are reviewed.
