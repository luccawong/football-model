# Post-Europe Market Residual Effect — Canonical Research Package

Status: `PASS / ADMIT`
Final research gate: `V3.2 FINAL ROBUSTNESS GATE`
Formal MODEL_1 feature: `post_europe_residual_flag`
Formal research name: `POST_EUROPE_MARKET_RESIDUAL_EFFECT`

## What this research establishes

Using 2021–2026 Titan history across the Premier League, La Liga, Serie A, Bundesliga and Ligue 1, this project tests whether a club's first domestic league match after UCL/UEL/UECL duty shows a residual performance penalty after controlling for opening-market strength and team identity.

Canonical exposure:
- first Big-Five domestic league match after an eligible European match;
- `0 < hours_since_europe <= 168`;
- post-Europe N = 1,833;
- same-club domestic control N = 8,672;
- 59 European-participating clubs.

Final V3.2 robustness result:
- adjusted non-win effect: `+0.0410` (+4.10pp);
- two-way cluster (team + domestic match): `p=0.0001`, 95% CI `(0.0205, 0.0615)`;
- within-team GEE logit: OR `1.204`, `p=0.0004`;
- wild-cluster bootstrap: `p<0.0001`;
- adjusted season sign consistency: `4/5` positive;
- adjusted league sign consistency: `5/5` positive;
- PPG residual: `-0.0715` points/match, `p=0.0014`;
- PPG residual direction: `5/5` seasons negative and `5/5` leagues negative.

## Interpretation discipline

This is a **market-residual feature**, not a universal causal fatigue coefficient. The research supports the statement that, conditional on the specified opening-market and team controls, the first domestic league match after Europe retains a measurable negative performance residual.

Do **not** mechanically subtract 4.1 percentage points or 0.0715 points from every eligible match. Those are historical research estimates, not fixed runtime weights.

Do not infer that the mechanism is fatigue. Historical lineup coverage is insufficient to separate fatigue, rotation, travel, prioritisation, squad depth or other mechanisms.

If both teams qualify, do not apply two independent fixed penalties. Compare relative schedule context and avoid double counting.

The calibration is validated only for the five leagues above. Other leagues/competitions are `NOT_CALIBRATED` unless separately validated.

## Findings not promoted by this study

- Shallow favourite AH failure: `WATCH` only; matched effect +3.8pp, p=0.253.
- TRUE_RETREAT × post-Europe: unresolved because the non-post retreat control sample is insufficient.
- Europe-away × league-away: rejected as a separate rule.
- UECL sandwich: rejected as a separate rule.
- Rest bucket: rejected as a standalone rule.
- XI carryover / rotation class: not validated because historical lineup data are unavailable.

## Canonical files

- `EURO_POST_LEAGUE_2021_2026_ROBUSTNESS_V3_2.md`
- `EURO_POST_LEAGUE_2021_2026_ACCEPTANCE_V3_2.md`
- `POST_EURO_EFFECT_BY_SEASON.csv`
- `POST_EURO_EFFECT_BY_LEAGUE.csv`
- `EURO_POST_LEAGUE_2021_2026_REPORT_V3_1_FINAL.md`
- `EURO_POST_LEAGUE_2021_2026_ACCEPTANCE_V3_1_FINAL.md`
- `EURO_POST_LEAGUE_2021_2026_V3_TO_V3_1_PATCH.md`
- `INTERNAL_CONSISTENCY_QC.csv`
- `ARTIFACT_MANIFEST.md`

Formal MODEL_1 policy overlay:
- `../../models/MODEL_1_EXTENSION_20260913_POST_EUROPE_RESIDUAL.md`
- `../../config/post_europe_residual_policy.json`
