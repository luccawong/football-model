# EURO POST LEAGUE — V3.2 FINAL ROBUSTNESS GATE 验收报告

## FINAL STATUS

**PASS**

## FINAL_MODEL_1_DECISION

**ADMIT**

## 关键验收数字（J 项）

| 指标 | 值 |
|---|---|
| ONE_WAY_CLUSTER_COEF | +0.0410 |
| ONE_WAY_CLUSTER_P | 0.0003 |
| TWO_WAY_CLUSTER_COEF | +0.0410 |
| TWO_WAY_CLUSTER_P | 0.0001 |
| FE_LOGIT_OR | 1.204 |
| FE_LOGIT_P | 0.0004 |
| WILD_CLUSTER_P | < 0.0001 |
| SEASON_POSITIVE_SIGN_COUNT | 4/5 |
| LEAGUE_POSITIVE_SIGN_COUNT | 5/5 |
| PPG_RESIDUAL_OVERALL | -0.0715 |
| PPG_SEASON_NEGATIVE_COUNT | 5/5 |
| PPG_LEAGUE_NEGATIVE_COUNT | 5/5 |
| FINAL_MODEL_1_DECISION | ADMIT |

## Final Gate 逐条判定（H 项）

| # | Gate | 结果 | 通过 |
|---|---|---|---|
| 1 | two-way cluster 负面方向 + CI 稳定 | coef +0.0410, p=0.0001, CI(0.020, 0.061) | ✓ |
| 2 | FE-logit/within-team 方向一致 | GEE OR=1.204, p=0.0004 | ✓ |
| 3 | wild-cluster 不推翻 | p<0.0001, CI(0.019, 0.063) | ✓ |
| 4 | 五赛季非单季驱动 | 4/5 正方向 | ✓ |
| 5 | 五联赛无反向异质性 | 5/5 正方向 | ✓ |
| 6 | PPG residual 方向一致 | -0.0715, 5/5+5/5 全负 | ✓ |

**6/6 通过。**

## 变量命名（G 项）

- 正式名称：**`POST_EUROPE_MARKET_RESIDUAL_EFFECT`**
- 定义：控制开盘市场胜率/盘口、球队身份、赛季及主客场后，欧战后首场国内联赛仍存在的剩余表现偏差。
- MODEL_1 接口字段：**`post_europe_residual_flag`**（不用 `post_europe_penalty`）

## 方法清单

- **A**：Two-way cluster（team_id + domestic_match_id），Cameron-Gelbach-Miller 修正
  - N_UNIQUE_DOMESTIC_MATCHES = 7453，N_DOUBLE_TEAMVIEW_MATCHES = 3052
- **B**：GEE logit（team FE + team grouping，exchangeable）
  - 注：ConditionalLogit 因 59 组大样本收敛慢，改用任务明确允许的 GEE 方案
- **C**：Wild cluster bootstrap（Rademacher，9999 iter，seed 20260913）
- **D**：五赛季独立 adjusted LPM（team + home + pwin + AH + cluster by team）
- **E**：五联赛独立 adjusted LPM（同口径）
- **F**：PPG_residual（team cluster + 按赛季 + 按联赛）

## 硬验收清单

- [x] two-way cluster 已做（team + match），与 one-way 并列比较
- [x] N_UNIQUE_DOMESTIC_MATCHES / N_DOUBLE_TEAMVIEW_MATCHES 已输出
- [x] FE-logit（GEE team FE+grouping）方向与 LPM 一致
- [x] 未继续使用"league+season 无 team FE"作为主要 robustness
- [x] wild cluster bootstrap >= 9999 iter，固定 seed
- [x] 五赛季 adjusted effect（非 RAW rate）已输出
- [x] 五联赛 adjusted effect 已输出
- [x] PPG_residual 按 season/league 分解
- [x] 变量正式命名为 POST_EUROPE_MARKET_RESIDUAL_EFFECT
- [x] 未重跑数据库、未改 pairing/AH/aggregate/异常日/浅盘 matched
- [x] 未为显著性更改模型、未 p-hacking、未扩大假设空间

## 数据约束

- 使用 V3.1 现有 10505 team-view comparator（1833 post + 8672 control）
- V3 canonical AH（Pinnacle），opening P(win)，season/team/home-away，domestic match_id
- 未复制 MATCH_LEVEL 文件
