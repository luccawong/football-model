# MODEL_1 — Current Default Football Model

Status: ACTIVE_DEFAULT
Effective date: 2026-09-09

This is the first formally registered football model in this repository. It is the default model for full pre-match analysis unless the user explicitly selects or creates another model.

## Purpose

MODEL_1 freezes the current football-analysis philosophy and execution rules so future model rebuilds can be compared against a stable historical baseline rather than silently rewriting the same model.

If MODEL_1 performance later fails to meet the user's expectations, do NOT overwrite its identity or retroactively change its historical outputs. Freeze MODEL_1 and create MODEL_2 with its own rules, activation date, records and validation.

## MODEL_1 fixed full-analysis order

1. Fundamentals
2. Market snapshot
3. Opening first impression
4. Opening rationality / lifecycle
5. Off-field factors / weather
6. Lineup / tactics
7. 1X2, including real-open vs camouflage-open audit after fundamentals
8. Asian handicap, including 1X2 -> AH European/Asian conversion consistency
9. Totals / OU
10. Cross-market coherence
11. Market attraction
12. External draw-exclusion website; EXCLUDED immediately opens winner-only audit, NOT_EXCLUDED triggers enhanced draw audit
13. Underdog outright audit
14. Correct score using repository Poisson / Dixon-Coles / Bayesian framework
15. Uncertainty audit
16. Freeze H1
17. Independent Red Team H2
18. Exactly one formal main ticket

## Fundamental layer requirements

Fundamentals are evaluated before market interpretation and must include, when data are available:

- recent match-by-match results, not just aggregate W-D-L;
- who each win came against and who each loss came against;
- opponent-quality weighting rather than treating all wins/losses equally;
- how the team won or lost: margin, game state, shot/xG/chance quality where available, home/away context and whether the result was repeatable;
- recent head-to-head only with context and recency, not as a standalone causal rule;
- future schedule and priority pressure;
- strength of opponents in the upcoming schedule;
- avoid arbitrary numerical weights until historically calibrated.

## Market interpretation constraints

- Opening-only first impression remains uncontaminated by later information.
- Real-open / camouflage-open classification is a prior/diagnostic layer, not a mechanical result rule.
- 1X2 must use de-vigged same-time company comparison.
- After 1X2, AH must explicitly test whether European and Asian market translation is coherent or conflicting.
- Favourite win probability must not be confused with deep-handicap cover probability.

## Draw-exclusion test

During the one-month forward test beginning 2026-09-09:

- `EXCLUDED=1` is a hard execution constraint: remove draw from the execution branch and immediately audit HOME WIN vs AWAY WIN.
- `NOT_EXCLUDED=0` is not a draw prediction, but draw receives enhanced mandatory audit.
- missing/unknown stays UNKNOWN.

## Underdog outright audit

- Mandatory for favourites -0.75 and deeper.
- Also central to winner-only review after draw exclusion.
- Compare WH, Ladbrokes, Bet365, Pinnacle, Interwetten, Macau and HKJC.
- Separate underdog AH cover evidence from outright-win evidence.
- U0/U1/U2/U3 grades describe upset-evidence quality, not absolute probability.

## Ticket policy

- Exactly one formal main ticket per fully analysed match.
- No non-main tickets.
- No final PASS under the current MODEL_1 policy; uncertainty is expressed by grade and execution conditions.
- Once an actionable ticket is issued it is locked; any change must be an explicit correction with old -> new.

## Research-only layers

- Betfair/OddsPapi Exchange: SHADOW_RESEARCH, zero formal impact.
- Macau post-2026-09-01 regime hypothesis: RESEARCH_ONLY.
- Uncalibrated divergence thresholds remain research until walk-forward validation supports promotion.
