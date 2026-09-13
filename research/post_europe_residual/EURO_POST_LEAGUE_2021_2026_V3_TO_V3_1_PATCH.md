# EURO POST LEAGUE — V3 → V3.1 PATCH NOTES

## 本轮性质

**只修统计口径一致性，不重跑数据库，不改变结论纪律。** 保留 V3 已正确的 canonical 定义。

## 修复摘要

| 项目 | V3 | V3.1 | 说明 |
|---|---|---|---|
| overall post N | 1833 | 1833 | 不变 |
| overall control N | 8672 | 8672 | 不变 |
| 逐赛季 control | 过期快照（合计 4772，与 overall 冲突）| 全量重算（合计 8672，自洽）| **A 项修复** |
| H1 整体 effect | -3.5pp（单一 RAW pooled）| RAW -3.5pp / **ADJUSTED +4.1pp (p=0.0003)** | **B 项拆分** |
| PPG_residual | 未分析 | **-0.0715 (cluster_p=0.0014)** | 新增关键指标 |
| 浅盘 effect | +3.8pp（混写 674/2996）| POOLED +5.9pp / MATCHED +3.8pp（488/978/186）| **C 项拆开** |
| aggregate 658 | 误称"first-leg leakage rows" | TOTAL_TWO_LEG_ROWS（非泄漏）| **D 项改名** |
| 异常日 p | V2 p=0.969（旧 AH）| V3 AH 重算 cluster_p=0.814 | **E 项重算** |
| `post_europe_flag` | REJECT | **ADMIT** | **G 项结论修正** |

## 关键根因（A 项）

V3 报告"跨赛季稳定性"表的 control rate（0.457/0.482/0.497/0.495/0.521）来自过期 season_effects 快照，其 control 合计 4772，与 overall 8672 冲突。

修复：从 `v3_comparator.pkl` 全量重算，得到正确逐赛季 control（1736/1819/1763/1692/1662，合计 8672），与 overall 完全自洽。

## 核心发现（B/G 项）

V3 的 REJECT 结论基于 RAW pooled 差（-3.5pp），这是一个**辛普森悖论**假象：欧战球队是强队，nonwin 基数低，直接 pooled 比较掩盖了真实效应。

ADJUSTED 分析（team FE + cluster SE）揭示：

1. **H1_ADJUSTED**：欧战后同一支球队 nonwin 概率 +4.1pp（z=3.64, p=0.0003）
2. **Logit 稳健性**：odds ratio = 1.17（p=0.0056）
3. **PPG_residual**：-0.071 points/场（cluster_p=0.0014），显著低于开盘市场预期

三条证据方向一致 → `post_europe_flag` = ADMIT。

## 逐项修复

### A. overall vs season
- 统一 control 定义：59 支欧战球队的全部国内非欧战比赛。
- Σ season post_N=1833，Σ season control_N=8672，加权 rate 与 overall 一致。

### B. H1 RAW / ADJUSTED
- RAW：-3.5pp（描述性）
- ADJUSTED：LPM `non_win ~ post_europe + home + p_team + AH + season + team FE`，cluster SE=team_id
- league 与 team 共线，由 team FE 吸收
- PPG_residual 单独分析

### C. 浅盘拆开
- POOLED：674 / 2996 → +5.9pp
- MATCHED：488 / 978 / 186 → +3.8pp（p=0.253）
- 488 + 186 = 674 已验证

### D. aggregate 改名
- 658 = TOTAL_TWO_LEG_ROWS（非泄漏）
- FIRST_LEG_ACTUAL_LEAK_BEFORE = NOT_RECONSTRUCTABLE
- FIRST_LEG_LEAK_AFTER = 0

### E. 异常日重算
- ANOMALY_V3_RECOMPUTED = TRUE
- AH fail diff +1.3pp，cluster_p=0.814

### F/G. 一致性 + 结论
- INTERNAL_CONSISTENCY_QC.csv 生成，全部 PASS
- `post_europe_flag` = ADMIT（REJECT → ADMIT）
