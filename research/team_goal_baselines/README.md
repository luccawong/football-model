# Titan 五大联赛球队进球基准（研究层）

这是一个独立于 MODEL_1 固定权重的研究层。输入只允许 Titan 完成赛果库；不会读取当前赔率来拟合球队强弱。

生成：

```powershell
python scripts/build_team_goal_baselines.py --db <titan数据库.sqlite>
```

产物 `database/research/team_goal_baselines.sqlite` 包含：

- `league_season_baselines`：赛季同期联赛主/客/总进球均值以及 GF/GA 基准；
- `team_season_stats`：球队 GF/GA、主客场 GF/GA 和样本量；
- `latest_team_baselines`：四种方案的攻击强度、防守失球因子和升降级分类；
- `backtest_predictions` / `backtest_metrics`：严格按开赛时间截断的逐场预测与训练/验证/测试指标；
- `team_aliases`：Titan team_id 到历史名称的稳定映射；
- `selected_variants`：每个联赛仅依据训练季选择的研究方案。

运行时使用：

```python
from gpt.team_goal_baseline import build_team_goal_baseline_packet

packet = build_team_goal_baseline_packet(
    competition_id="36", home_team="19", away_team="20",
    quant_packet=model_1_quant_packet,
)
```

返回值带有 `research_only=true` / `formal_model_1_weight_impact=NONE`。当传入 MODEL_1 的 Titan 1X2+OU `quant_packet` 时，会输出 `market_goal_residual`（市场净胜球差减历史净胜球差）和 `market_total_residual`（市场总进球减历史总进球），并保留主/客 λ 残差。
