# MODEL_1 Final Pre-Freeze Audit — 2026-09-10 Beijing Time

Status: FINALIZED_BEFORE_ONE_MONTH_FREEZE
Freeze: 2026-09-10 through 2026-10-10 Asia/Shanghai

## Final additions recovered from prior cross-chat rules

1. League opening baseline is not a generic strength-to-handicap formula. Prefer league-specific historical opening calibration.
2. HFA structure is `league HFA baseline + team home/away residuals`; do not double-count a generic home advantage plus a second generic away penalty.
3. Old rough `~10 rating points ~= 1 goal` remains seed-only, never a fixed MODEL_1 conversion.
4. Historical opening calibration should prefer same-company mapping: HKJC opening 1X2 de-vig -> HKJC opening Asian main line, avoiding cross-company time and alternate-line contamination.
5. Opening-band deviation of 0.25 handicap step = `REVIEW_REQUIRED`; >=0.50 = `STRUCTURAL_ANOMALY_ALERT`. These are diagnostic flags only and cannot directly create a ticket.
6. High-grade tickets require correspondingly high information completeness/coherence; low-information competitions, unconfirmed lineups or missing key timelines widen uncertainty/can cap grade, but under current policy still do not create final PASS.
7. Quick scan for Champions League/high-profile events should not discard a match solely because structure is unclear; retain a direction plus structure grade for deep-analysis selection.
8. Stage 5 weather must be visibly output every full analysis; `WEATHER_DATA_MISSING` is required when reliable weather cannot be verified.
9. Stage 5 now explicitly covers heat/humidity, altitude/acclimatization, rain/wind, pitch/drainage/roof, long-haul/time-zone/body-clock effects, two-leg aggregate incentives, national-team continuity/chemistry, manager/morale hypotheses and club relationship/reciprocity networks.
10. Same-day off-field digest should be checked when available, while later official information overrides earlier reporting.

## Screenshot heuristic disposition

Accepted as qualitative/evidence-conditioned context:
- R55 human/relationship risk concept;
- R57 two-leg aggregate-state concept;
- R133 manager/morale/letdown concept;
- R139 national-team continuity/chemistry concept;
- R144 club relationship-network concept;
- R85 heat/humidity;
- R86 altitude;
- R87 combined heat/humidity stress;
- R134 acclimatization duration;
- R135 rain/wind;
- R140 home geography/climate familiarity as residual beyond HFA;
- R141 travel/body-clock/circadian context.

Rejected as fixed MODEL_1 rules:
- universal one-grade downgrade for narrative risk;
- first-leg lead >=2 mechanically means relax/trailing team becomes the direction;
- new manager +1 / complacency -0.5 / season-end relaxation -1;
- fixed same-club-player-count chemistry bonuses/penalties;
- S/A/B club-bond +1.0/+0.5/+0.3;
- heat/humidity universal xG or goal debuff;
- altitude second-half attack x0.7;
- fixed acclimatization multipliers by day bucket;
- rain small/medium/heavy = -0.5/-1/-1.5 goals;
- kickoff morning/afternoon/late-night fixed penalties;
- rest >=6 days automatically reduces attack by 0.2;
- opaque R88 V1/V2/V3/V4 tactical-counter weights without definitions/validation.

## One-month freeze behavior

During the freeze, MODEL_1 formal semantics do not change from wins/losses or newly suggested heuristics.

Allowed:
- Titan/raw data collection;
- results/statistics updates;
- parser/QC/identity bug fixes that restore the frozen behavior;
- tests for already-frozen rules;
- logging research ideas under `research/pending_model_2/`.

Not allowed unless user explicitly ends the freeze:
- new formal modules;
- new thresholds/weights;
- new source authority;
- promotion of Shadow/Research signals;
- stage reordering;
- alteration of ticket, draw-exclusion or Red Team semantics.

## Remaining intentionally unresolved / not admitted

- 'European player UEFA signal' has been referenced in prior workflow discussion but does not yet have a precise, falsifiable rule definition. It is not silently converted into a MODEL_1 weight.
- R88 tactical V1/V2/V3/V4 labels are undefined in the supplied screenshot, so they are not admitted.

These can be researched/logged during the freeze for potential MODEL_2, with zero impact on MODEL_1.
