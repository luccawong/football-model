# EURO POST LEAGUE — V3.1 FINAL CONSISTENCY HOTFIX 验收报告

## FINAL STATUS

**PASS**

（数字一致性全部通过；结论修正方向 REJECT → ADMIT 是口径修复的必然结果，非"为 PASS 修改结论"。）

## 本轮范围

只修"统计口径一致性"，不重新跑数据库。保留 V3 已正确的 canonical 定义。

## 一致性核心数字（四份文档统一引用，单一来源 `_v31_results.json`）

| 指标 | 值 |
|---|---|
| overall post_N | 1833 |
| overall control_N | 8672 |
| overall post nonwin rate | 0.5139 |
| overall control nonwin rate | 0.5485 |
| H1_RAW diff | -3.5pp |
| H1_ADJUSTED post_europe coef | +0.0410 |
| H1_ADJUSTED p | 0.0003 |
| H1_ADJUSTED z | 3.639 |
| Logit OR | 1.1683 |
| Logit p | 0.0056 |
| PPG_residual diff | -0.0715 |
| PPG_residual cluster_p | 0.0014 |
| SHALLOW_POOLED post_N | 674 |
| SHALLOW_POOLED control_N | 2996 |
| SHALLOW_POOLED effect | +5.9pp |
| SHALLOW_MATCHED post_N | 488 |
| SHALLOW_MATCHED control_N | 978 |
| SHALLOW_MATCHED unmatched | 186 |
| SHALLOW_MATCHED effect | +3.8pp |
| SHALLOW_MATCHED cluster_p | 0.253 |
| FIRST_LEG_ROWS | 332 |
| SECOND_LEG_ROWS | 326 |
| TOTAL_TWO_LEG_ROWS | 658 |
| NON_TWO_LEG_ROWS | 1175 |
| ANOMALY_DAYS_TOTAL | 57 |
| ANOMALY_DAYS_WITH_POST_EURO | 20 |
| ANOMALY_POST_EURO_N | 159 |
| ANOMALY AH fail diff | +1.3pp |
| ANOMALY cluster_p | 0.814 |
| ANOMALY favorite nonwin | 58/128 (0.4531) |
| NORMAL favorite nonwin | 493/1174 (0.4199) |
| ANOMALY dog win | 8/27 (0.2963) |
| NORMAL dog win | 74/326 (0.2270) |

## A — overall vs season 冲突已修复

- 根因：过期 season_effects 快照（control 合计 4772）与 overall（8672）冲突。
- 修复：从 `v3_comparator.pkl` 全量重算，Σ season post_N=1833、Σ season control_N=8672，加权 rate 与 overall 完全一致。
- **PASS**

## B — H1 RAW / ADJUSTED 已拆分

- H1_RAW：-3.5pp（混杂，仅描述）
- H1_ADJUSTED：LPM + team FE + cluster SE，coef=+0.0410，p=0.0003
- 稳健性：logit OR=1.1683，p=0.0056
- PPG_residual：-0.0715，cluster_p=0.0014（显著低于市场预期）
- **PASS**

## C — 浅盘 pooled / matched 已拆开

- SHALLOW_POOLED：674 / 2996，+5.9pp
- SHALLOW_MATCHED：488 / 978 / 186，+3.8pp，p=0.253
- 验证 488 + 186 = 674 ✓
- **PASS**

## D — Aggregate Leakage 命名已修正

- 658 = TOTAL_TWO_LEG_ROWS（两回合语义样本总数），**不是** leakage 数
- FIRST_LEG_ACTUAL_LEAK_BEFORE = NOT_RECONSTRUCTABLE
- FIRST_LEG_LEAK_AFTER = 0
- **PASS**

## E — 异常日 V3 AH 重算完成

- ANOMALY_V3_RECOMPUTED = TRUE
- AH fail diff +1.3pp，cluster_p=0.814，不显著
- **PASS**

## F — 一致性 QC

- INTERNAL_CONSISTENCY_QC.csv 已生成，所有指标 PASS。
- 任何一项不一致 → FINAL STATUS = FAIL（未触发）。

## G — 结论纪律

- H1_ADJUSTED 完成后判定：`post_europe_flag` = **ADMIT**（V3 的 REJECT 修正）。
- RAW 不显著/反向但 ADJUSTED 显著 → 不能 REJECT（本轮正是此情形）。

## MODEL_1_RECOMMENDATION（V3.1）

- **ADMIT**：`post_europe_flag`
- **WATCH**：`ah_depth_bucket`（浅盘）
- **CONTEXT_ONLY**：`true_retreat`
- **REJECT**：`europe_away×league_away`、`uecl_sandwich_flag`、`rest_bucket`、`xi_carryover`、`rotation_class`

## 硬验收清单

- [x] overall 与 season 使用同一 control 定义（数学自洽）
- [x] H1 拆 RAW 与 ADJUSTED，不再混用"同一批球队"声称
- [x] H1_ADJUSTED 含 team FE + cluster SE（team_id）
- [x] PPG_residual 单独分析（post vs nonpost）
- [x] 浅盘 pooled 与 matched 彻底拆开（674/2996 vs 488/978/186）
- [x] 488 + 186 = 674 已验证
- [x] aggregate 658 不再冒充 leakage 数
- [x] FIRST_LEG_ACTUAL_LEAK_BEFORE = NOT_RECONSTRUCTABLE
- [x] 异常日使用 V3 AH 重算（ANOMALY_V3_RECOMPUTED=TRUE）
- [x] 四份文档数字统一（单一 JSON 来源）
- [x] INTERNAL_CONSISTENCY_QC.csv 生成
