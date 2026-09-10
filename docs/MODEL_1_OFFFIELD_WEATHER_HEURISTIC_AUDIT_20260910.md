# MODEL_1 Off-field / Weather Heuristic Audit — 2026-09-10

Status: FINAL_PRE_FREEZE_AUDIT
Formal policy: accepted concepts are implemented qualitatively in `config/off_field_weather_policy.json`; rejected fixed coefficients are not part of MODEL_1.

## Screenshot rules reviewed

### 3.6 Human / tacit / psychology

- R55 人情/默契综合处理 — **PARTIAL ACCEPT**. Relationship/reciprocity and motivation are valid context categories, but a universal 'high-risk scene -> downgrade one grade' rule is rejected. A downgrade requires material evidence affecting match path/pricing/cover ability.
- R57 次回合比赛方向锁 — **PARTIAL ACCEPT**. Aggregate score and qualification incentives belong in Stage 5, but 'first-leg margin >=2 -> winner relaxes / loser attacks' is not deterministic and is not a formal direction lock.
- R133 心理/情绪因子 — **PARTIAL ACCEPT**. Manager change, morale rebound, complacency and end-season motivation may be considered as evidence-conditioned hypotheses. Fixed +1/-0.5/-1 adjustments are rejected.
- R139 国家队默契度/化学反应 — **PARTIAL ACCEPT**. Continuity, shared-club/cohort familiarity, training time, coach tenure and lineup turnover are valid context. Fixed player-count thresholds and +0.5/-0.5 weights are rejected.
- R144 俱乐部羁绊分级 — **PARTIAL ACCEPT**. Club relationship/network evidence remains active; S/A/B automatic numeric adjustments are rejected.

### 3.7 Environment / climate / geography

- R85 气候 Debuff — **PARTIAL ACCEPT**. Heat/humidity stress is valid, but universal expected-goal multiplication is rejected.
- R86 高原 Debuff — **PARTIAL ACCEPT**. Altitude and acclimatization are valid; automatic second-half x0.7 is rejected.
- R87 高温轻微综合征 — **PARTIAL ACCEPT**. Combined heat/humidity risk is valid; automatic one-grade downgrade is rejected.
- R134 高原/气候适应梯度 — **PARTIAL ACCEPT**. Arrival/acclimatization duration matters, but fixed 3-day/7-day multipliers are rejected until calibrated.
- R135 雨战/风战量化 — **PARTIAL ACCEPT**. Rain, wind, gusts, drainage and standing water are mandatory weather checks when relevant. Fixed -0.5/-1/-1.5 goal penalties are rejected; heavy rain does not mechanically mean Under.
- R140 东道主地理优势量化 — **PARTIAL ACCEPT**. Crowd, geography, altitude/climate familiarity and travel/cultural adaptation may matter only as residual context beyond existing HFA. Double-counting is forbidden.
- R141 开赛时间与生物钟 — **PARTIAL ACCEPT**. Transmeridian travel, body-clock mismatch, arrival time and sleep/recovery are valid. Fixed morning/afternoon/late-night penalties are rejected.
- R145 '歇大了'效应 — **REJECT AS FIXED RULE**. Rest >=6 days is not automatically an attacking penalty. Review training rhythm and context case by case.
- R88 战术克制权重 — **NOT ADMITTED**. The V1/V2/V3/V4 definitions are not sufficiently specified. Tactical counters belong in Stage 6 and require explicit definitions/validation before any fixed weighting.

## General MODEL_1 rule

Environmental and human factors are evidence-conditioned path modifiers, not automatic score/probability/grade adjustments. They may alter a formal conclusion only when supported by identifiable facts plus a plausible mechanism and, where applicable, coherent Titan pricing. Generic narrative risk alone is not enough.

## Freeze consequence

These decisions are frozen into MODEL_1 through 2026-10-10 Beijing time. New coefficients or heuristics discovered during the freeze are logged under `research/pending_model_2/` with zero formal impact.
