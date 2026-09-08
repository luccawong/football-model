# DATABASE SCHEMA

数据库：`database/draw_exclusion.db`（本地生成、Git 忽略）

DDL：`database/schema.sql`

Schema version：1.0

## Identity and snapshots

### `matches`

一场研究比赛一行。主键 `research_match_id` 是以下字段规范化后进行 SHA-256：

```text
competition + home_team + away_team + kickoff_time_with_timezone
```

`data-idx` 不参与 ID。`titan_match_id` 只有确定性 resolver 返回单一结果时才写入。

### `website_snapshots`

每次 HTTP 抓取一行，保存 UTC/北京时间、HTTP Date、Last-Modified、页面更新时间、SHA-256、文件大小、原始 HTML 相对路径和同日内容版本。相同内容的再次抓取仍生成独立 snapshot，不覆盖原始文件。

### `snapshot_diffs`

将同日当前 snapshot 与前一 snapshot 比较，记录：

- `added_rows`
- `deleted_rows`
- `label_changed_rows`
- `odds_changed_rows`
- `details_json`

身份字段变化会按删除 + 新增处理，避免错误拼接。

### `website_labels`

每个 snapshot、research match、source market 一行。保存二元 Teacher 标签、网站行号、原始 `data-key`、比赛编号和单关标志。复合主键允许同一真实比赛分别保留竞彩/北单观察。

### `site_visible_odds`

与 `website_labels` 一对一，保存页面公开的 1X2、AH 数值/原文和两侧水位。空值表示页面没有提供，不做插值。

## Resolution and external markets

### `match_resolutions`

保存每次 Titan 匹配审计：`resolved`、`ambiguous`、`not_found` 或 `unavailable`，以及候选、匹配方法和来源验证包。歧义时不猜测 Titan ID。

### `external_1x2`

完整 1X2 事件流：公司、`odds_time`、主/平/客十进制赔率、quote role、来源记录 ID 和完整原始 JSON。

### `external_ah`

完整亚洲盘事件流：公司、时间、盘口、主客价格、quote role 和原始 JSON。

### `external_ou`

完整大小球事件流：公司、时间、盘口、大小球价格、quote role 和原始 JSON。

三个事件表均使用内容派生的 `event_id` 去重；不会把不同时间或不同盘口的事件压缩成 opening/current 两点。

## Truth, features, and models

### `final_results`

只保存最终比分与派生 Truth：`is_draw`、`home_win`、`away_win`、`result_1x2`。这些字段不出现在赛前市场表。

### `feature_snapshots`

按比赛、`feature_time` 和 feature version 冻结特征，并保存 `minutes_to_kickoff`、`opening_validity` 和版本化 JSON。未来 builder 必须拒绝使用晚于 `feature_time` 的赔率事件。

### `model_outputs`

预留 Draw Exclusion Layer 输出：draw probability、exclusion probability、四级分类、Teacher agreement、正反证据、冲突和置信度。胜负方向模型不放入此表。

### `rule_candidates`

保存候选规则、样本量、Teacher precision、真实不平率、联赛分布和 Failure Conditions，用于后续 Red Team。

### `teacher_evaluation` view

将 Teacher 标签与 Truth 左连接。只有 Teacher label=1 且赛果已存在时计算：

```text
non-draw -> teacher_exclusion_success = 1
draw     -> teacher_exclusion_success = 0
```

未排平对照行保持 NULL，不误写成 Teacher 失败。

## Integrity rules

- 所有核心表启用外键。
- 标签、布尔字段、概率和分类都有 CHECK 约束。
- 快照 HTML 路径唯一；每个 snapshot 的每个市场观察唯一。
- 数据库采用 WAL；写入使用事务。
- 跨表时间无可移植 SQL CHECK，未来 feature builder 必须在应用层强制 `odds_time <= feature_time < kickoff_time`。
