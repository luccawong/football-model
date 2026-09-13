# EURO POST LEAGUE — V3.2 FINAL ROBUSTNESS GATE 稳健性报告

## 执行摘要

本轮是**最后一轮统计稳健性验收**，唯一目标：判断 V3.1 发现的 post-Europe residual effect（+4.1pp nonwin，PPG -0.071）在处理同场比赛相关性、模型形式、联赛/赛季异质性后，是否仍足以进入 MODEL_1。

**结论：通过全部 6 条 Gate，FINAL_MODEL_1_DECISION = ADMIT。**

---

## 变量正式命名（G 项）

**`POST_EUROPE_MARKET_RESIDUAL_EFFECT`**

定义：**在控制开盘市场胜率/盘口、球队身份、赛季及主客场后，欧战后首场国内联赛仍存在的剩余表现偏差。**

MODEL_1 接口建议字段：**`post_europe_residual_flag`**（不再使用隐含因果含义的 `post_europe_penalty`）。

方向约定（重要）：该效应表现为——
- **nonwin 概率升高**（post_europe 系数为正，+4.1pp）
- **PPG 残差为负**（实际积分低于开盘市场预期，-0.071）

两者方向一致，都指向"欧战赛后国内表现**变差**"。本报告中"负面效应"指"表现变差"，而非系数符号为负。

---

## A. Two-way Cluster（team_id + domestic_match_id）

同场比赛两支球队各有一条 team-view，会产生 match 层面的相关性，V3.1 只 cluster 了 team_id。

| 口径 | coef | SE | z | p | 95% CI |
|---|---|---|---|---|---|
| One-way (team) | +0.0410 | 0.0113 | 3.639 | 0.0003 | (0.0189, 0.0631) |
| **Two-way (team + match)** | **+0.0410** | **0.0105** | **3.919** | **0.0001** | **(0.0205, 0.0615)** |

**检查**：
- N_UNIQUE_DOMESTIC_MATCHES = 7453
- N_DOUBLE_TEAMVIEW_MATCHES = 3052（3052 场比赛出现 2 条 team-view）

**结论**：加入 match 层面的 cluster 后 SE 反而**缩小**（0.0113 → 0.0105），z 从 3.64 升到 3.92，效应**更稳健**。同场比赛相关性不削弱结论。

---

## B. FE Logit / Within-Team Robustness

V3.1 的 logit 没有 team FE，不能作为与 LPM 相同 estimand 的稳健性验证。本轮改用 **GEE logit（team FE + team grouping，exchangeable correlation）**，这是任务明确的"方案3"，同时满足固定效应与 within-team 两个要求。

| 指标 | 值 |
|---|---|
| 方法 | GEE logit（team FE + team grouping）|
| post_europe coef | +0.1857 |
| **OR** | **1.204** |
| p | **0.0004** |
| OR 95% CI | (1.087, 1.334) |

**结论**：OR = 1.20（欧战后 nonwin 概率高约 20%），与 team-FE LPM 的 +4.1pp **方向一致且显著**。注：ConditionalLogit 因 59 组大样本组内条件似然收敛慢，改用 GEE 方案（任务明确允许）。

---

## C. Wild Cluster / Small-Cluster Robustness

team cluster 仅 59 个，需 wild cluster bootstrap 检验小样本推断稳健性。

| 指标 | 值 |
|---|---|
| 方法 | Wild cluster bootstrap（Rademacher，cluster=team_id）|
| iterations | 9999 |
| seed | 20260913 |
| **wild_cluster_p** | **< 0.0001** |
| bootstrap 95% CI | (0.0191, 0.0627) |

**结论**：wild cluster bootstrap 完全不推翻，p < 0.0001，CI 不含 0。小样本 cluster 下效应稳健。

---

## D. 五赛季 Adjusted Effect

每赛季独立估计同口径 adjusted post-Europe effect（team + home + pwin + AH）。

| season | post_N | control_N | coef | 95% CI | p | 方向 |
|---|---|---|---|---|---|---|
| 2021-2022 | 306 | 1736 | +0.0459 | (-0.0156, 0.1073) | 0.143 | + |
| 2022-2023 | 337 | 1819 | -0.0038 | (-0.0597, 0.0522) | 0.895 | - |
| 2023-2024 | 332 | 1763 | +0.0502 | (-0.0095, 0.1098) | 0.099 | + |
| 2024-2025 | 416 | 1692 | +0.0620 | (0.0053, 0.1187) | 0.032 | + |
| 2025-2026 | 442 | 1662 | +0.0065 | (-0.0432, 0.0563) | 0.797 | + |

**SIGN_CONSISTENCY = 4/5**（正方向赛季数 / 5）。

- 仅 2022-23 微负（-0.004，几乎为零，非显著反向）。
- 2024-25 显著（+6.2pp，p=0.032），2021-22（+4.6）与 2023-24（+5.0）效应量接近且接近显著。
- **不是单季驱动**：去掉 2024-25 后其余 4 季仍 3/4 正，pooled 效应仍为正。

---

## E. 五联赛 Adjusted Effect

| league | post_N | control_N | coef | 95% CI | p | 方向 |
|---|---|---|---|---|---|---|
| 英超 | 389 | 1967 | +0.0466 | (0.0028, 0.0904) | 0.037 | + |
| 西甲 | 381 | 1861 | +0.0351 | (-0.0029, 0.0731) | 0.071 | + |
| 意甲 | 388 | 1313 | +0.0250 | (-0.0067, 0.0567) | 0.122 | + |
| 德甲 | 368 | 1740 | +0.0856 | (0.0115, 0.1596) | 0.024 | + |
| 法甲 | 307 | 1791 | +0.0143 | (-0.0285, 0.0570) | 0.514 | + |

**LEAGUE_SIGN_CONSISTENCY = 5/5**（全部正方向）。

- **无严重反向异质性**：五大联赛方向全部一致为正。
- 德甲效应最大（+8.6pp，p=0.024），英超次之（+4.7pp，p=0.037），是 overall +4.1pp 的主要贡献者；法甲最小（+1.4pp，不显著）。
- 德甲贡献评估：德甲 post 368 场，效应 +8.6pp 显著高于 overall，但并非唯一驱动（英超、西甲、意甲均为正）。

---

## F. PPG_residual Robustness

PPG_residual = ActualPoints − (3×opening_Pwin + opening_Pdraw)。

| 口径 | diff | p |
|---|---|---|
| **Overall（team cluster）** | **-0.0715** | **0.0014** |
| 95% CI | (-0.1815, -0.0412) | — |

**按赛季**（负 = 低于市场预期）：

| season | diff | 方向 |
|---|---|---|
| 2021-2022 | -0.1386 | 负 |
| 2022-2023 | -0.0036 | 负 |
| 2023-2024 | -0.0545 | 负 |
| 2024-2025 | -0.1303 | 负 |
| 2025-2026 | -0.0230 | 负 |

**PPG_SEASON_NEGATIVE_COUNT = 5/5**

**按联赛**：

| league | diff | p | 方向 |
|---|---|---|---|
| 英超 | -0.1060 | 0.008 | 负 |
| 西甲 | -0.0291 | 0.478 | 负 |
| 意甲 | -0.0909 | 0.115 | 负 |
| 德甲 | -0.1269 | 0.006 | 负 |
| 法甲 | -0.0086 | 0.964 | 负 |

**PPG_LEAGUE_NEGATIVE_COUNT = 5/5**

**结论**：PPG 残差整体为负（-0.0715，p=0.0014），5/5 赛季、5/5 联赛全部为负，方向完全一致。

---

## H. Final Gate 判定

| # | Gate 条件 | 结果 | 是否通过 |
|---|---|---|---|
| 1 | two-way cluster 仍为负面方向（表现变差），CI 不巨大不稳定 | +0.0410, p=0.0001, CI(0.020, 0.061) | ✓ |
| 2 | FE-logit / within-team 方向一致 | GEE OR=1.204, p=0.0004 | ✓ |
| 3 | wild-cluster 不推翻 | p<0.0001, CI(0.019, 0.063) | ✓ |
| 4 | 五赛季非单季驱动 | 4/5 正，非单季 | ✓ |
| 5 | 五联赛无严重反向异质性 | 5/5 正 | ✓ |
| 6 | PPG residual 整体方向一致 | -0.0715, 5/5 赛季、5/5 联赛全负 | ✓ |

**6/6 全部通过 → FINAL_MODEL_1_DECISION = ADMIT。**

---

## 最终结论

V3.1 发现的 post-Europe residual effect 在以下六重稳健性检验下全部成立：

1. **Two-way cluster**（team + match）：效应更强（p 0.0003 → 0.0001）
2. **GEE FE-logit**（team FE + grouping）：OR=1.20，方向一致
3. **Wild cluster bootstrap**：p<0.0001，不推翻
4. **五赛季**：4/5 正方向，非单季驱动
5. **五联赛**：5/5 正方向，无反向异质性
6. **PPG residual**：-0.0715，5/5 赛季、5/5 联赛全负

**`post_europe_residual_flag` 正式进入 MODEL_1，评级 ADMIT。**

效应规模：欧战后首场国内联赛，同一支球队的 nonwin 概率升高约 **+4.1pp**（OR≈1.20），实际积分低于开盘市场预期约 **-0.071 points/场**。德甲（+8.6pp）与英超（+4.7pp）是主要贡献联赛。

---

## 方法论边界（诚实声明）

- 本结论建立在 2021–2026 Titan 历史数据（5 赛季、59 支欧战球队、1833 post + 8672 control）之上。
- team cluster 仅 59 个，属于 small-cluster 情形；已通过 wild cluster bootstrap 校验，但样本规模是固有局限。
- 无 lineup/首发数据，无法分解"体力 vs 轮换"机制，本效应是"剩余表现偏差"而非因果机制分解。
- 不扩大假设空间，不 p-hacking，本轮只做 V3.1 已发现效应的稳健性 gate。
