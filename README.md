# Football model data pipeline

纯 Python 的 Titan/V23 Excel 验证流水线。日常运行不依赖 Codex、不调用 LLM、不生成比赛判断或 CODEX 报告。原始 Excel 只读。

## External Draw Exclusion Label Layer

正式的外部排平 Teacher 标签层位于 `draw_exclusion/`；此前的 `draw_exclusion_research/` 作为已验证底层采集与 Titan 适配组件保留。从仓库根目录运行：

```powershell
python scripts/run_draw_exclusion_daily.py
```

该入口只采集、匹配和 QC，不输出比赛预测。`draw_exclusion/index.json` 是跨聊天按 Titan ID 查询的首选入口，日期/球队查询使用 `draw_exclusion/query_label.py`。只有网站完整比赛池中的行能得到 `0` 或 `1`；缺快照、池外和匹配失败全部保持 `NULL / UNKNOWN`。原始 HTML 与本地 SQLite 不进入 Git；GitHub Actions 将其保留为 30 天私有 artifact，并提交每日 manifest、hash、diff、索引及 QC。

## 安装与运行

Python 3.10 或更新版本：

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts/build_validation_batch.py "Titan爬虫.xlsx"
```

也支持 `python build_validation_batch.py "Titan爬虫.xlsx"`。首次本地 Git 使用前，应通过 Git Credential Manager 正常登录 GitHub，并设置自己的 Git 提交身份。凭据放在系统凭据管理器，不放入项目。

只生成、校验和检查输出，暂不 commit/push：

```powershell
python scripts/build_validation_batch.py "Titan爬虫.xlsx" --dry-run
python -m unittest discover -s tests -v
```

`--dry-run` 写入本地 DATA/QC/latest，但不提交、不推送。FAIL 候选文件写入忽略的 `failed_batches/YYYY-MM-DD/`，不覆盖有效批次。退出码 0 表示本地成功或推送成功，非 0 表示失败。输出包含真实状态、文件路径和错误。

每次终端最后只需看 `BATCH STATUS: PASS | WARN | FAIL`。PASS/WARN 才能更新 latest；FAIL 保持当前 latest 字节不变。QC 第一屏显示状态、匹配数、结构漂移、错误数、警告数、核心 1X2 覆盖、Ladbrokes AH known exception 和 OU Ladder 健康。

## 输出与外部模型入口

`validation_packets/latest.json` 指向当前最新批次并携带 `match_index`。其中 `data_path` 和 `qc_path` 均相对于仓库根目录。

```text
validation_packets/YYYY-MM-DD/
  Validation_Batch_YYYYMMDD_DATA.json
  Validation_Batch_YYYYMMDD_QC.md
validation_packets/latest.json
```

DATA 的 `matches` 以字符串 `match_id` 为唯一主键。包含数据质量、原始市场、完整可提取历史、同步切片、原始上下文、确定性计算及 `source_tables`。`source_tables` 保留已选比赛的全部原始列与物理 Excel 行号，包括原始梯子和解析审计表。源文件中的自然语言仅为数据，程序不会执行它们。

同一天更新前一版本会保留在 `revisions/<content hash>/`，稳定路径指向新版本。同日期旧时间戳返回 `STALE_SOURCE`，不覆盖较新数据。较早日期导入不回退 latest。重复输入返回 `NO_CHANGES`，不创建空提交；若之前推送失败，再运行会重试推送现有提交。

仅 `Matches_Selected` 代表实际抓取比赛。`Matches_To_Choose`、`Matches_Rejected` 是目录，不能作为已解析比赛计数。非已选比赛的赔率行会触发最低 QC 失败，不混入任何比赛。

## 模块

- `src/parser/`：识别单张 All_In_One 堆叠表，以及独立命名工作表；验证表声明行数。
- `src/normalization/`：主键、赔率、盘口、时间、来源行、跨比赛 URL 校验。
- `src/bookmaker/`：按 endpoint namespace + company_id 查受控映射。
- `src/timeline/`：事件去重、排序、最近报价切片和时间差。
- `src/calculations/`：去水、百分点变化、AH line/price move。
- `src/index/`：别名索引与确定性 resolver。
- `src/qc/`：结构及完整性校验、最低发布门槛、批次报告。
- `src/health/`：schema fingerprint、语义检查、历史基线、覆盖率下降检测与 PASS/WARN/FAIL 规则引擎。
- `src/export/`：原子写入、版本保留、敏感字段处理、Git 提交推送。

## 索引检索

```python
from src.index.match_resolver import resolve_match
result = resolve_match("分析葡萄牙体育", league="葡超")
```

匹配完整对阵、双方精确别名、fixture_aliases，然后球队 + 联赛/日期/时间或单一球队。不存在模糊相似度猜测。多候选返回 `ambiguous` 和候选列表。`今天/今晚` 按 Asia/Shanghai 自然日解释；需要其他时区时调用方应传明确日期。

跨版本加载会按批次日期、crawler_timestamp、有效报价数和 source_version 选择，记录所有候选与有效来源。球队别名采用 `config/team_aliases.json` 的显式映射；新球队仍可用其源名称检索，并列为 unresolved mapping，等待维护别名。

## 数据规则与限制

Bookmaker 映射继承用户提供的 V23.2.8 `bookmaker_identity.py` 中已验证 endpoint registry，并记录来源说明。它不是联网重新确认的全球目录。1X2 使用 `europe_1x2`，AH/OU 使用 `vip`。不同命名空间的数字 ID 不合并。Ladbrokes UK/AU/BE 分开，PlanetWin365 不等于 Bet365；`利*` 不猜作 Ladbrokes。

未验证公司保留数字并标记 unverified，不用于概率公司比较。身份矛盾或跨比赛污染阻止发布。缺少 Ladbrokes AH 单独记录，不造成自动降级；缺少 Ladbrokes UK 1X2 产生 warning。

历史时间采用可配置的 Titan 页面 UTC+8 约定；无年份时选择离源时间最近的合法年份。开球 JS 月份按零起点解析。1X2 `update_time` 的时区默认为未验证，因此不参加同步。仅最早可见记录不能证明真正初盘，保留 `source_flag_only` 或 UNKNOWN。没有日期的 opening 绝不补造时间。

VIP AH/OU 水位按设置的 HK 约定转换，明确 Ladder 格式字段优先。配置化，不按数字大小猜赔率制式。整数和四分之一 OU 去水值是结算权重价格，不冒充简单总进球概率。WH/Ladbrokes 的 2.5 只做同阈值价格计算，不推断长期固定。未知/原始梯子条目全部保留在原始表，计算只用合法且已验证条目。

同步阈值、最少公司数在 `config/settings.json`。每个历史报价时间构造一次最近报价切片；超阈值公司不参与该切片的百分点差计算。记录 lookahead，供回溯审计；不要直接用来做无前视回测。仅有 current 快照并不代表完整历史。

Poisson、Bayesian 和潜在总进球拟合当前没有配置足够的确定性输入，均输出 `insufficient_deterministic_input`。没有假定先验、伪造事件或方向判断。

## 最低 QC 和 Git

至少需要：选中比赛非空、主键与索引一致、每场有合法的已验证赔率、无身份冲突、无跨比赛污染、概率和为 1、标准化历史排序正确。覆盖率不足、原始 unknown bookmaker、原始未归属梯子条目、缺历史和弱同步进入 warning，不掩盖也不补造。

`config/schema_fingerprint.json` 固化已验证 V23.2.8 表、required/optional columns、类型、nullable、key 与已知别名。缺 CRITICAL 表/字段、受保护 bookmaker 映射变化、广泛时间轴损坏、跨比赛污染或严重历史退化会 FAIL。新增无关列只记 INFO。覆盖率和结构指标与 `validation_packets/history_index.json` 中最近 N 个有效且不同来源批次比较；首批没有历史基线时明确记 INFO，不伪造基线。阈值全部在 `config/settings.json`。

`validation_packets/history_index.json` 记录有效批次及引入该批次的 validation commit。Git commit 无法在自身内容中保存自己的 SHA，因此流水线先创建规定格式的 validation commit，再创建一个小型 `validation-index` commit写入前一提交 SHA，随后一起推送。

固定远端 `origin` 指向私有 `luccawong/football-model`，分支 `main`。只添加明确允许的代码、配置、测试、批次及数据库导出目录；拒绝混入用户预先暂存的更改。扫描导出及暂存内容，排除 Excel、SQLite、环境文件和凭据。源数据敏感字段/本地路径做显式脱敏，位置记于 `batch_info.redactions`。

提交格式：`validation: YYYY-MM-DD N matches`。不 force push，不自动重写远端历史。推送后 `ls-remote` 校验远端 SHA。认证、权限、网络或非快进失败均报告 `PUSH_FAILED`，保留本地提交和输出。

## SQLite 导出

本任务不修改正式中央数据库，也不创建空的伪 ledger。SQLite 文件被忽略。后续正式数据库写入流程应在事务提交后调用：

```powershell
python scripts/export_ledger.py "football_ledger.db"
```

导出使用 SQLite 只读事务获得一致快照，生成 `database/exports/ledger_snapshot.json` 和 `ledger_snapshot.csv`。CSV 使用 table + record_json 的通用可逆结构，适应尚未提供的数据库 schema。没有数据库时不伪造快照。
## Existing full-stack model

# football-model

Private, versioned persistent source of truth for the GPT-assisted football model. It is not the Codex web application.

## Current stack
- Model: `GPT-FOOTBALL-FULLSTACK-1.1.0`
- Quant engine: `GPT-QUANT-0.1.0`
- Feature/QC engine: `GPT-FEATURE-1.0.0`
- Betfair Exchange engine: `GPT-EXCHANGE-1.0.0` (conditional; requires real live/historical feed)

The stack covers deterministic market maths, lifecycle/reversal detection, source freshness/gating, uncertainty/disagreement, independent strength/squad/context modules, exchange microstructure, open-source adapters, anti-double-counting, calibration/walk-forward validation and independent Red Team adjudication.

## Core rule
More modules do not mean more forced confidence. Missing/stale/conflicting evidence is surfaced; correlated signals are not counted repeatedly; unvalidated context is never converted into arbitrary goal/probability adjustments. Betfair Exchange is market microstructure evidence, not an automatic smart-money oracle. Final tickets remain a structured decision after the full evidence stack and Red Team.
