# Context Utility & Market Distortion — Research Protocol

Date: 2026-09-14
Model: MODEL_1 targeted extension research support
Formal effect: audit semantics only; no fixed numeric weights are authorised by this research file.

## Objective

Validate which parts of the 2026-09-14 context/market extension have reproducible pre-match information value beyond existing MODEL_1 strength and Titan market inputs.

The protocol is designed to reject seductive narratives if they do not survive time-safe controls.

## Core anti-leakage rule

Every feature must be reconstructable using information available before the target snapshot/kickoff. No final standings, final prize outcome, post-match lineup knowledge, closing prices substituted for earlier snapshots, or post-result media explanations may enter a historical feature.

## Study A — Price vs popularity distortion

### Questions

1. Do teams with high narrative attraction receive systematically different 1X2 pricing after controlling for strength?
2. Is the effect different in AH?
3. Does a price move that resists the attractive side contain incremental information after controlling for opening probability and line state?
4. Do hot-hand and name/sentiment effects survive walk-forward testing?

### Inputs

- Titan opening and timestamped 1X2/AH/OU.
- De-vig probabilities and same-time cross-company differences.
- Pre-match team form and public narrative features available at the time.
- Genuine public ticket/handle shares only if a future explicitly authorised source is available; otherwise they remain absent, not imputed.
- Betfair/OddsPapi only under its existing shadow-research authority.

### Outcomes

- 1X2 residual versus market probability.
- AH settlement residual at the quoted line.
- movement-to-result calibration.
- Brier/RPS/log loss change versus baseline where probabilistic outputs exist.

### Controls

League, season, team strength, home advantage, opening probability bin, price level, favourite class, match importance and snapshot time.

### Critical falsifier

If the apparent signal disappears after conditioning on opening probability/strength or reverses materially across seasons, it is not promoted.

## Study B — Competitive Match Importance

### Feature construction

For each team before each match, enumerate realistic sporting endpoints under current competition rules:

- title;
- automatic promotion;
- playoff entry/seeding;
- UEFA qualification tier;
- relegation survival;
- knockout/league-phase advancement or seeding.

Construct W/D/L counterfactual states and estimate the change in feasibility/probability of each endpoint. Do not use final-season knowledge.

### Candidate outputs

- `sporting_marginal_value_win_vs_loss`
- `sporting_marginal_value_draw_vs_loss`
- `objective_saturation_state`
- `dead_rubber_candidate`

`dead_rubber_candidate` is not a rank label. It is allowed only when all meaningful endpoints have minimal marginal movement and no separate verified incentive overrides the state.

### Primary tests

- Does low marginal importance predict lineup rotation, lower core-player minutes or altered odds after controlling for team strength?
- Does it predict market residual or result residual out of sample?
- Are effects league-specific?

### Midtable falsifier

If simple table rank performs as well as or better than the counterfactual objective model, the additional complexity is not justified.

## Study C — Schedule / priority / venue quadrants

### Sequence separation

Analyse PRE_EUROPE and POST_EUROPE separately.

### Venue interaction states

- domestic home / Europe away
- domestic away / Europe home
- domestic home / Europe home
- domestic away / Europe away

### Required covariates

- exact recovery hours;
- travel distance/time-zone exposure when material;
- opponent strength in both matches;
- European competition and stage;
- current domestic sporting marginal value;
- next European sporting marginal value;
- squad depth / replacement quality;
- player minutes in 14d/21d where reconstructable;
- actual announced lineup only when known by target snapshot.

### Existing MODEL_1 constraint

The already-promoted `post_europe_residual_flag` must be included as an explicit baseline. Do not claim a venue interaction effect that is merely the existing post-Europe residual rediscovered in another variable.

### Models

Use team/season controls and clustered or repeated-measures methods where appropriate. Compare pooled estimates with league-specific and club-strength interactions.

### Promotion rule

A venue quadrant is not promoted as a standalone direction unless it demonstrates stable incremental value beyond rest, opponent strength, match importance, squad depth and the existing post-Europe effect.

## Study D — Financial marginal match value

### Data hierarchy

1. official current-season league/competition distribution rules;
2. official competition circulars;
3. club financial statements or official disclosures;
4. high-quality reporting for verified bonuses/distress;
5. unverified rumours excluded from quantitative features.

### Candidate feature

Expected financial value is computed as the change in expected future award under W/D/L, not as the total prize pool.

Where possible, retain both raw currency value and a scale relative to revenue/wage bill, but do not pick a universal transformation until validation.

### Tests

- incremental prediction of lineup/rotation decisions;
- incremental prediction of market repricing after sporting importance is controlled;
- interactions with verified liquidity stress.

### Falsifier

If financial value adds no information after sporting marginal importance, keep it descriptive and do not double count it.

## Study E — Relationship / integrity risk

### Principle

This study tests whether verifiable relationship features have incremental predictive or market-residual value. It does **not** infer corruption from correlation.

### Structured relationship graph

Nodes: clubs, owners, directors, coaches, sporting directors, agents/intermediaries where lawfully/publicly documented, academies, feeder/satellite entities.

Edges:

- common control/ownership;
- shared director/decisive influence;
- repeated loans/transfers;
- formal academy/satellite agreement;
- documented management/agent network;
- documented financial/commercial dependency.

### Required separation

- `relationship_present`
- `relationship_strength_evidence_tier`
- `asymmetric_table_need`
- `market_residual_anomaly`
- `specific_reciprocity_evidence`

No feature may collapse these into a single "friendly clubs" label.

### Historical testing

Where a large enough clean sample exists, compare related-club matches with matched controls on team strength, table incentive, venue, season, league and market probability. Examine result and market residuals separately.

### Critical false-positive guard

A significant related-club coefficient is not sufficient to claim coordination. Plausible confounding through shared recruitment, style, ownership investment or information quality must be tested first.

## Validation framework

For every study:

- chronological train/validation/test split;
- no random shuffle as primary evidence;
- season-by-season coefficient/effect stability;
- league-specific heterogeneity report;
- missingness audit;
- negative controls/placebos where possible;
- compare against the current MODEL_1 baseline, not against a weak naive model;
- record both statistical uncertainty and betting/decision relevance;
- preserve all failed hypotheses rather than deleting them after results are known.

## Promotion ladder

1. `RESEARCH_ONLY`
2. `SHADOW_TRACE`
3. `ACTIVE_FORMAL_AUDIT_NO_FIXED_WEIGHT`
4. `CALIBRATED_FORMAL_FEATURE`
5. fixed numeric decision adjustment only with explicit user authorisation

The 2026-09-14 extension begins at level 3 for audit semantics; unvalidated sub-effects such as PRE_EUROPE venue quadrants remain level 1-2 inside that audit.
