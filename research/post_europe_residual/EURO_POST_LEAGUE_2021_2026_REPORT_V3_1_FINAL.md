# EURO POST LEAGUE 2021–2026 — V3.1 FINAL CONSISTENCY HOTFIX 研究报告

## 执行摘要

本轮 **V3.1 只修"统计口径一致性"**，不重新跑数据库，不改变 V3 已经正确的 canonical 定义（post=1833、control=8672、Pinnacle AH、synthetic AH=0、two-leg aggregate 语义、57 异常日清单、match pairing/rest/sandwich）。

在把"整体效应"从**单一 RAW nonwin 差**拆成 **RAW 与 ADJUSTED 两套口径**之后，核心结论发生了**方向性修正**：

> **V3 声称"欧战赛程压力无独立效应（REJECT）"是错的。** 那是因为 V3 只看了 RAW 的 pooled 差（-3.5pp），没有做 ADJUSTED 分析。一旦控制球队固定效应（team FE）+ 赛季 + 主场 + 开盘胜率 + AH，**欧战后同一支球队的 nonwin 率显著升高 +4.1pp（z=3.64, p=0.0003）**，且 **PPG 残差显著为负 -0.071（cluster_p=0.0014）**，即欧战球队赛后表现**低于开盘市场预期**。

这是一个典型的**辛普森悖论**：欧战球队本身是强队（nonwin 基数低），直接 pooled 比较会掩盖"同一支球队欧战后变弱"的真实效应。

---

## 一、A — 修复 H1 overall vs Season 数学冲突（根因已查明）

### 根因

V3 报告的"跨赛季稳定性"表（control rate = 0.457 / 0.482 / 0.497 / 0.495 / 0.521）来自一个**过期的 season_effects 快照**，其 control 合计仅 **4772**，与 overall 的 **8672** 冲突（五个赛季 control rate 全部 ≤0.521，却声称 overall=0.549，数学上不可能同时成立）。

正确口径（从 `v3_comparator.pkl` 全量重算，同一 control 定义）：

| season | post_N | post_nonwin | post_rate | control_N | control_nonwin | control_rate |
|---|---|---|---|---|---|---|
| 2021-2022 | 306 | 157 | 0.5131 | 1736 | 921 | 0.5305 |
| 2022-2023 | 337 | 160 | 0.4748 | 1819 | 1001 | 0.5503 |
| 2023-2024 | 332 | 173 | 0.5211 | 1763 | 958 | 0.5434 |
| 2024-2025 | 416 | 224 | 0.5385 | 1692 | 923 | 0.5455 |
| 2025-2026 | 442 | 228 | 0.5158 | 1662 | 954 | 0.5740 |

### 验证

- Σ season post_N = **1833** ✓（== overall）
- Σ season control_N = **8672** ✓（== overall）
- Σ post_nonwin / Σ post_N = **0.5139** ✓（== overall 0.5139）
- Σ control_nonwin / Σ control_N = **0.5485** ✓（== overall 0.5485）

**结论：overall 与 season 现在使用同一 control 定义（59 支欧战球队的全部国内非欧战比赛），数学完全自洽。**

---

## 二、B — H1 拆分 RAW 与 ADJUSTED

### H1_RAW（原始 pooled 差，仅供描述）

| 指标 | post | control | diff |
|---|---|---|---|
| N | 1833 | 8672 | — |
| nonwin 场 | 942 | 4757 | — |
| nonwin rate | 0.5139 | 0.5485 | **-3.5pp** |

RAW 显示欧战后 nonwin 率**更低**（-3.5pp），但这是**混杂**：欧战球队是强队，nonwin 基数天然低。

### H1_ADJUSTED（控制球队身份后的独立效应）

**模型**：LPM（线性概率模型）

```text
non_win ~ post_europe + home_away + p_team + AH + season + team_FE
```

- cluster-robust SE，cluster unit = team_id（59 teams）
- league 与 team 完全共线，由 team FE 吸收，故不单独列 league dummy
- n_obs = 10505，n_features = 67（满秩 rank=67）

| 项 | 系数 | se | z | p |
|---|---|---|---|---|
| **post_europe** | **+0.0410** | 0.0113 | 3.639 | **0.0003** |
| home (is_home) | +0.0187 | 0.0120 | — | 0.1196 |
| p_team | -0.9210 | 0.1426 | — | <0.0001 |
| AH (teamview) | +0.0209 | 0.0265 | — | 0.4304 |

**稳健性对照（logit，league+season，无 team FE）**：

- post_europe coef = +0.1556，p = 0.0056，**odds ratio = 1.1683**

两个模型方向一致且均显著：**欧战后 nonwin 概率升高约 +4.1pp（LPM）/ OR=1.17（logit）。**

### PPG_residual（是否低于开盘市场预期）

```text
PPG_residual = ActualPoints - (3 × opening_Pwin + opening_Pdraw)
```

| 组 | mean PPG_residual | cluster_p | CI(2.5%–97.5%) |
|---|---|---|---|
| post | **-0.0230** | — | — |
| control | +0.0485 | — | — |
| **diff** | **-0.0715** | **0.0014** | (-0.1815, -0.0412) |

**欧战球队赛后国内比赛实际积分显著低于开盘市场预期（-0.071 points/场，cluster_p=0.0014）。**

---

## 三、C — 浅盘 pooled 与 matched 彻底拆开

### SHALLOW_POOLED（描述性，混杂）

| 指标 | 值 |
|---|---|
| post_N | 674 |
| control_N | 2996 |
| post_fail | 373（0.5534）|
| control_fail | 1481（0.4943）|
| effect | **+5.9pp** |

pooled 的 +5.9pp 混杂了球队身份，**不作正式结论**。

### SHALLOW_MATCHED（正式结果）

| 指标 | 值 |
|---|---|
| matched_post_N | 488 |
| matched_control_N | 978 |
| unmatched_post_N | 186 |
| matched_post_fail | 275（0.5635）|
| matched_control_fail | 510（0.5215）|
| effect | **+3.8pp** |
| cluster_p | 0.253 |
| CI(2.5%–97.5%) | (-0.027, +0.097) |

**验证：488 + 186 = 674 ✓**

matched 的 +3.8pp 在 cluster bootstrap 下**不显著**（p=0.253），列为 WATCH。禁止把 2996 control N 与 +3.8pp matched effect 写在同一指标。

---

## 四、D — Aggregate Leakage QC 命名修正

| 项 | 值 |
|---|---|
| FIRST_LEG_ROWS_TOTAL | 332 |
| SECOND_LEG_ROWS_TOTAL | 326 |
| TOTAL_TWO_LEG_ROWS | **658**（=332+326，两回合语义样本总数，**不是泄漏数**）|
| NON_TWO_LEG_ROWS_TOTAL | 1175（1168 not_applicable + 7 single）|
| FIRST_LEG_ACTUAL_LEAK_BEFORE | **NOT_RECONSTRUCTABLE**（V2 旧值无法精确恢复）|
| FIRST_LEG_LEAK_AFTER | 0 |

**658 是"two-leg 语义样本总数"，不是"first-leg future leakage rows"。V3 报告的错误命名已修正。**

---

## 五、E — 异常日用 V3 AH 重算

**ANOMALY_V3_RECOMPUTED = TRUE**（使用 V3 Pinnacle canonical AH + V3 settlement 重算，替代 V2 的 p=0.969 旧值）。

| 指标 | 异常日 | 正常日 | diff | cluster_p |
|---|---|---|---|---|
| post-Europe N | 159 | 1674 | — | — |
| AH fail | 80（0.5031）| 821（0.4904）| +1.3pp | 0.814 |
| AH cover | 65（0.4088）| 735（0.4391）| -3.0pp | — |
| favorite nonwin | 58/128（0.4531）| 493/1174（0.4199）| +3.3pp | — |
| dog win | 8/27（0.2963）| 74/326（0.2270）| +6.9pp | — |

- 异常日总数 = **57**，其中 20 天有 post-Europe 暴露（159 场）。
- 异常日 AH fail 率（50.3%）与正常日（49.0%）差异 +1.3pp，cluster_p=0.814，**不显著**。
- favorite nonwin（+3.3pp）与 dog win（+6.9pp）方向一致地显示异常日"冷门偏多"，但样本小（dog N=27），不作正式结论。
- 结论与 V2 方向一致（无统计关联），但现在是 V3 AH 口径下的重算结果。

---

## 六、F/G — 结论纪律与最终评级

只有 H1_ADJUSTED 完成后才能判定 `post_europe_flag` 评级。

| 证据 | 值 | 判断 |
|---|---|---|
| H1_RAW diff | -3.5pp | 混杂（强队基数），不可用 |
| H1_ADJUSTED coef | +4.1pp, p=0.0003 | 显著正效应 |
| Logit 稳健性 | OR=1.17, p=0.0056 | 显著正效应 |
| PPG_residual diff | -0.071, cluster_p=0.0014 | 显著低于市场预期 |

**双向证据一致 → `post_europe_flag` = ADMIT**（从 V3 的 REJECT 修正）。

### MODEL_1 准入建议（V3.1）

| 字段 | 评级 | 理由 |
|---|---|---|
| `post_europe_flag` | **ADMIT** | ADJUSTED +4.1pp（p=0.0003）+ PPG_residual -0.071（p=0.0014）双向显著 |
| `ah_depth_bucket`（浅盘） | **WATCH** | matched +3.8pp 但 p=0.253 不显著，跨赛季不稳定 |
| `true_retreat` | **CONTEXT_ONLY** | 独立市场风险信号，与 post-Europe 无增量 |
| `europe_away × league_away` | **REJECT** | 客场效应不显著 |
| `uecl_sandwich_flag` | **REJECT** | 内部比较仅 +1.5pp |
| `rest_bucket` | **REJECT** | ≤96h 无差异 |
| `xi_carryover` / `rotation_class` | **REJECT** | LINEUP_HISTORY_UNAVAILABLE |

---

## 七、方法论说明

1. **RAW vs ADJUSTED 不可混用**：RAW 的 -3.5pp 与 ADJUSTED 的 +4.1pp 是不同口径，分别回答"欧战球队 vs 全市场"和"同一支球队欧战前后"两个不同问题。
2. **辛普森悖论**：欧战球队是强队（p_team 系数 -0.921 说明开盘胜率每 +10% nonwin 降 9.2pp），直接 pooled 比较必然低估欧战的真实效应。
3. **cluster SE**：cluster unit = team_id（59 teams），因 league 与 team 共线，league 由 team FE 吸收。
4. **PPG_residual**：用开盘 de-vig 概率作为"市场预期积分"基准，残差衡量球队相对市场预期的超/欠表现，是判断"赛程压力是否导致低于预期"的更直接指标。
