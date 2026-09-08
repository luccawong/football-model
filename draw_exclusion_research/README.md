# Draw Exclusion Research Pipeline

该目录实现第二阶段 Week 1：只采集、匹配和 QC，不训练模型、不生成比赛判断。

## 每日运行

在 `football-model` 仓库根目录执行：

```powershell
python scripts/run_draw_exclusion_daily.py
```

运行会：

1. 读取排平网站完整静态 HTML；
2. 将每次原始响应追加保存到 `raw/draw_site/YYYY-MM-DD/`；
3. 解码竞彩和北单排平索引，同时保留所有未排平对照行；
4. 写入本地 SQLite `database/draw_exclusion.db`；
5. 使用仓库现有 Titan 精确/别名 resolver 尝试匹配；
6. 对成功匹配的比赛导入验证包中的完整 1X2/AH/OU 时间轴；
7. 生成或更新 `reports/daily/YYYY-MM-DD.md`。

原始 HTML 和 SQLite 被 Git 忽略，但保留在本机；代码、schema、日报和文档进入版本控制。配置中不保存网站密码，因为第一阶段已经确认完整 HTML 可通过普通 GET 获取，门禁只在前端显示层生效。

## 测试

```powershell
python -m unittest tests.test_draw_exclusion -v
python -m unittest discover -s tests -v
```

## 当前边界

- 不进行模糊队名猜测；歧义比赛保留 `ambiguous`。
- 不从网站历史正样本训练分类器。
- 不从比分构造赛前特征。
- 不把 `data-idx` 当永久 ID。
- 不覆盖旧 HTML；同日内容变化产生新的 `content_version` 和行级 diff。
- 当前仓库没有 OddsPapi/Betfair 在线客户端，因此这些覆盖率会如实为 0，直至合法模块或数据到位。
