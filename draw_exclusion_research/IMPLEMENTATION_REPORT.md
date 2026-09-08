# IMPLEMENTATION REPORT

## Outcome

第二阶段 Week 1 基础管线已经建立。系统现可冻结网站当日竞彩和北单完整比赛池，保存不可覆盖的原始 HTML，将二元 Teacher 标签和未排平对照组写入 SQLite，尝试匹配现有 Titan 索引，导入成功匹配比赛的完整市场时间轴，并生成每日 QC 报告。

本次没有建立预测模型、正式排平规则或赛果方向模型。

## REUSE

以下 `football-model` 现有模块直接复用，没有复制其逻辑：

| 模块 | 复用方式 |
|---|---|
| `src.index.match_index_builder.normalize` | NFKC/casefold/空白标准化；用于稳定 ID 和数据库标准化字段 |
| `src.index.match_resolver.MatchResolver` | Titan match_id 的确定性精确/别名解析；不启用模糊相似度猜测 |
| `src.index.match_resolver.load_index` | 从已有验证包选择每个 Titan 比赛的最佳来源版本 |
| `src.normalization.formats.line_value` | 把网站中文 AH 盘口转换为主队视角的四分之一球数值 |
| Titan `validation_packets/*_DATA.json` | 读取已通过 QC 的比赛身份、1X2/AH/OU 标准化时间轴和公司身份 |
| 现有 bookmaker registry | 继续使用 namespace-qualified 公司名，不混淆 Bet365/PlanetWin365 或 Ladbrokes 地区实例 |
| 已有 `timeline` / `calculations` 结构 | 外部事件直接导入标准化赔率与原始 JSON，不丢弃时间轴 |

现有仓库审计结果：

- 有 Titan/V23 Excel 解析与 QC，但没有今天实时抓取源文件的在线调度器。
- 有 1X2、AH、OU、多公司、时间轴、去水、同步切片和公司差异计算。
- 有 William Hill、Ladbrokes UK、Macau、Pinnacle、Bet365、Interwetten 的受控映射；HKJC 存在于 VIP 映射，可用于 AH/OU。
- 没有可调用的 OddsPapi 客户端。
- 没有可调用的 Betfair 客户端。
- 最新验证包日期为 2026-09-05，只含 2 场 2026-09-06 比赛，因此无法覆盖 2026-09-08 网站池。

## MODIFY

| 文件 | 修改 |
|---|---|
| `.gitignore` | 忽略本地原始网站快照；已有规则继续忽略 SQLite |
| `requirements.txt` | 增加 BeautifulSoup 4，用于结构化解析静态 HTML |
| `README.md` | 增加 Draw Exclusion 管线入口说明 |
| `scripts/run_draw_exclusion_daily.py` | 增加与仓库现有脚本风格一致的每日入口 |

现有 Titan 解析、QC、导出和发布逻辑未被改写。

## NEW

### Website layer

- `crawler/draw_site_collector.py`：只读 GET；记录 HTTP Date、Last-Modified 和抓取时刻。
- `crawler/draw_site_parser.py`：严格解码 `_mk`，解析竞彩/北单所有当前行，生成稳定 `research_match_id`。
- `crawler/snapshot_manager.py`：每次保存原始 HTML；同日相同 hash 不覆盖，同日新 hash 增加 content version。

### Storage layer

- 完整 SQLite schema 和 repository。
- 网站快照、标签、可见赔率、Titan 解析审计、外部 1X2/AH/OU 时间轴、赛果、特征、模型输出、候选规则分别存表。
- `snapshot_diffs` 比较同日相邻快照的新增、删除、标签和可见赔率变化。
- `teacher_evaluation` 视图只在赛果到位后计算排平成功，不把 Truth 写入特征表。

### Integration and reporting

- `integration/titan_adapter.py`：复用现有 resolver 和验证包，匹配后导入完整 timeline。
- `reports/daily.py`：按竞彩/北单分别报告样本、Teacher 标签和覆盖率，完整列出所有未匹配行。
- `tests/test_draw_exclusion.py`：覆盖标签正/负组、ID 稳定性、版本不覆盖、SQLite 外键和标签完整性。

## First live run

抓取页面：2026-09-08 页面版本 1。

| QC | 数量 |
|---|---:|
| 网站当前比赛行 | 97 |
| 竞彩 | 12 |
| 竞彩排平 | 8 |
| 北单 | 85 |
| 北单排平 | 14 |
| 全部排平 | 22 |
| 全部未排平 | 75 |
| Titan 成功匹配 | 0 |
| 网站可见 1X2 | 12 |
| 网站可见 AH | 87 |
| 外部 1X2/AH/OU | 0/0/0 |

0 Titan 匹配不是解析失败。现有 Titan validation packet 的比赛日期与网站比赛池不重叠；全部 97 行均已保留并在日报列出。

## Missing / deferred

以下内容因数据或阶段限制尚未实现，未用占位假数据掩盖：

- 当日 Titan 原始 Excel/实时 crawler 输入；现有仓库只有 2026-09-05 验证包。
- OddsPapi 和 Betfair 客户端或授权数据。
- 最终赛果自动补全源。
- T-24h/T-12h/T-6h/T-3h/T-1h/T-30m 赔率调度；数据库已支持事件时间轴。
- same-time-slice 的 5/10 分钟研究特征生成；仓库现有同步模块可复用，但需当日外部赔率到位。
- Week 2–4 的统计、Teacher imitation、SHAP、规则提取和 Red Team。

## Audit and leakage guarantees

- 原始 HTML 和每次 hash 永久追加，不覆盖。
- 网站标签按抓取时刻冻结；后续赔率不会回写 Teacher 标签。
- 网站排平和未排平行同时保存。
- 竞彩与北单分别保留 source market。
- `site_row_index` 只作证据，不作主键。
- 外部赔率保留 `odds_time`、公司、market、line、price、原始 JSON 和来源记录 ID。
- 赛果只进入 `final_results`；特征表不包含比分列。
