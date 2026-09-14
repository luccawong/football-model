# Five-League Team Goal Baseline Research Protocol

Scope: Premier League, La Liga, Serie A, Bundesliga, Ligue 1.
Primary historical window: 2021-22 through 2025-26 completed seasons.
Current-season extension: 2026-27 YTD stored separately and marked partial.
Status: research/shadow until validation and explicit promotion.

## Goal

Build long-run team scoring and conceding baselines that can support MODEL_1 fundamentals and score-distribution priors without introducing stale-team, promotion/relegation, home/away, or league-environment bias.

The raw quantity proposed by the user — Team A average goals minus Team B average goals — should be stored, but only as a descriptive field. The stronger production candidate compares each team's attack with the opponent's defence after league and venue normalization.

## Raw match fields

For every top-flight league match in scope store competition, season, match date, home team canonical ID/name, away team canonical ID/name, home goals, away goals, and source.

Do not mix cup, European, or lower-division matches into the top-flight baseline table.

## Team-season outputs

For each team and season calculate matches played, GF per match overall, GA per match overall, home GF per match, home GA per match, away GF per match, away GA per match, total-goals per match, goal-difference per match, sample size, and coverage flags.

For each league-season calculate league home GF per match, league away GF per match, league total goals per match, and home/away split.

## Normalized strength indices

home_attack_strength = team_home_GF_per_match / league_home_GF_per_match

away_attack_strength = team_away_GF_per_match / league_away_GF_per_match

home_defence_weakness = team_home_GA_per_match / league_away_GF_per_match

away_defence_weakness = team_away_GA_per_match / league_home_GF_per_match

## Matchup baseline

For home team A versus away team B:

lambda_home_baseline = league_home_GF_per_match * A_home_attack_strength * B_away_defence_weakness

lambda_away_baseline = league_away_GF_per_match * B_away_attack_strength * A_home_defence_weakness

matchup_goal_gap = lambda_home_baseline - lambda_away_baseline

matchup_total_baseline = lambda_home_baseline + lambda_away_baseline

Also store:

raw_average_GF_gap = A_long_run_GF_per_match - B_long_run_GF_per_match

normalized_attack_gap = A_attack_index - B_attack_index

## Time and recency discipline

Do not pool all seasons into one undifferentiated number and call it current strength.

Build and compare at least:
1. five-season unweighted baseline;
2. two-season rolling baseline;
3. recency-weighted multi-season baseline;
4. current-season baseline shrunk toward league/team historical means;
5. venue-specific versions.

Select recency weights by out-of-sample validation, not intuition.

## Promotion/relegation handling

Top-flight and lower-division goal environments must remain separate unless an empirically validated translation is created. If no translation exists, use top-flight history when available and shrink sparse current top-flight data toward the league mean. Store promoted/relegated status explicitly.

## Small samples

Use empirical-Bayes or another transparent shrinkage method toward the relevant league/venue mean when samples are small. Do not create a universal minimum-match cutoff without validation.

## Entity normalization

Create a canonical team mapping so translated or renamed club names do not split one club into multiple records. Preserve original source names for audit.

## Validation

Historical features must be time-safe: for a match on date D, use only matches before D.

Evaluate candidate baselines using Poisson deviance or log-likelihood for home and away goals, MAE/RMSE for total goals and goal difference, calibration of goal-count buckets, correct-score support as a secondary metric, and stability by league and season.

Compare against simple league-average and current MODEL_1 market-only score priors. A more complex baseline should not be promoted unless it improves out-of-sample performance.

## MODEL_1 placement if promoted

If validation succeeds, place the layer in Stage 1 fundamentals and Stage 14 score-prior construction as a prior/context feature. It must not overwrite Titan market information.

No fixed AH, grade, or ticket adjustment is authorised by this research protocol.
