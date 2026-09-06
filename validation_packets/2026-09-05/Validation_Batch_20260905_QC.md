# Batch Health

STATUS: WARN

Matches: 2/2
Schema drift: NONE
Critical errors: 0
Warnings: 9
Latest update: YES (after local acceptance)
Git push: PENDING AFTER QC

Core 1X2 coverage:
William Hill: 2/2
Ladbrokes UK: 2/2
Interwetten: 2/2
Pinnacle: 2/2
Bet365: 2/2
Macau: 2/2

AH Ladbrokes:
KNOWN_EXCEPTION

OU Ladder:
2/2 complete

## Health events

| Severity | Code | match_id | Details |
|---|---|---|---|
| WARN | CONFLICTING_DUPLICATE | 2910885 | {"groups":7,"sample":[{"market":"1x2","bookmaker_key":"europe_1x2:281","timestamp":"2026-09-04T00:22:00+00:00","line":null,"distinct_quotes":2},{"market":"1x2","bookmaker_key":"europe_1x2:281","timestamp":"2026-09-04T00:51:00+00:00","line":null,"distinct_quotes":2},{"market":"1x2","bookmaker_key":"europe_1x2:281","timestamp":"2026-09-04T01:44:00+00:00","line":null,"distinct_quotes":2},{"market":"1x2","bookmaker_key":"europe_1x2:281","timestamp":"2026-09-04T02:51:00+00:00","line":null,"distinct_quotes":2},{"market":"1x2","bookmaker_key":"europe_1x2:281","timestamp":"2026-09-05T03:03:00+00:00","line":null,"distinct_quotes":2}]} |
| WARN | NEW_OR_UNVERIFIED_BOOKMAKER | 2910885 | {"record_count":310} |
| WARN | NEW_OR_UNVERIFIED_BOOKMAKER | 3023474 | {"record_count":312} |
| WARN | PARTIAL_TIMELINE | 2910885 | {"broken":1,"total":14} |
| WARN | PARTIAL_TIMELINE | 3023474 | {"broken":1,"total":14} |
| WARN | SYNCHRONIZED_SLICES_WEAK | 2910885 | {"status":"WEAK","aligned":11,"total":190,"ratio":0.05789473684210526} |
| WARN | SYNCHRONIZED_SLICES_WEAK | 3023474 | {"status":"WEAK","aligned":55,"total":346,"ratio":0.15895953757225434} |
| WARN | TIMELINE_SOURCE_REVERSE_ORDER | 2910885 | {"groups":20,"company_markets":["1x2:europe_1x2:104","1x2:europe_1x2:1135","1x2:europe_1x2:115","1x2:europe_1x2:1350","1x2:europe_1x2:177","1x2:europe_1x2:281","1x2:europe_1x2:80","1x2:europe_1x2:82","1x2:europe_1x2:986","ah:vip:1"]} |
| WARN | TIMELINE_SOURCE_REVERSE_ORDER | 3023474 | {"groups":23,"company_markets":["1x2:europe_1x2:104","1x2:europe_1x2:1135","1x2:europe_1x2:115","1x2:europe_1x2:1350","1x2:europe_1x2:177","1x2:europe_1x2:281","1x2:europe_1x2:432","1x2:europe_1x2:80","1x2:europe_1x2:82","1x2:europe_1x2:986"]} |
| INFO | HISTORICAL_BASELINE_UNAVAILABLE | batch | {} |
| INFO | LADBROKES_AH_KNOWN_EXCEPTION | 2910885 | {} |
| INFO | LADBROKES_AH_KNOWN_EXCEPTION | 3023474 | {} |

## Schema fingerprint

- Version：v23.2.8-validation-1
- Tables checked：13
- Tables observed：35
- Schema drift：NONE

## Coverage monitor

| Market | Company | Current | Previous valid baseline | Delta |
|---|---|---:|---:|---:|
| 1x2 | William Hill | 100.0% | N/A | N/A |
| 1x2 | Ladbrokes UK | 100.0% | N/A | N/A |
| 1x2 | Interwetten | 100.0% | N/A | N/A |
| 1x2 | Pinnacle | 100.0% | N/A | N/A |
| 1x2 | Bet365 | 100.0% | N/A | N/A |
| 1x2 | Macau | 100.0% | N/A | N/A |
| ah | Macau | 100.0% | N/A | N/A |
| ah | Pinnacle | 100.0% | N/A | N/A |
| ah | Bet365 | 100.0% | N/A | N/A |
| ah | HKJC | 100.0% | N/A | N/A |
| ah | Crown | 100.0% | N/A | N/A |
| ou | Macau | 100.0% | N/A | N/A |
| ou | Pinnacle | 100.0% | N/A | N/A |
| ou | Bet365 | 100.0% | N/A | N/A |
| ou | William Hill Base-2.5 | 50.0% | N/A | N/A |
| ou | Ladbrokes Base-2.5 | 100.0% | N/A | N/A |

## Historical health baseline

- Baseline available：False
- Baseline sample count：0
- Average bookmakers/match：23.0
- Average timeline rows/match：{"1x2": 353.0, "ah": 275.5, "ou": 228.0}
- Average core OU Ladder lines/company：4.0
- Unverified bookmaker row rate：0.23605313092979127
- Duplicate row rate：0.0
- Missing timestamp rate (history)：0.0

## 比赛索引

| match_id | league | fixture | kickoff | status |
|---|---|---|---|---|
| 3023474 | 葡超 | 葡萄牙体育 vs 葡萄牙国民 | 2026-09-06T03:30:00+08:00 | pre_match |
| 2910885 | 巴西甲 | 圣保罗 vs 米内罗竞技 | 2026-09-06T05:30:00+08:00 | pre_match |

## 1X2 Coverage

| Company | Coverage | Missing match_id |
|---|---|---|
| William Hill | 2/2 (100.0%) | none |
| Ladbrokes UK | 2/2 (100.0%) | none |
| Interwetten | 2/2 (100.0%) | none |
| Pinnacle | 2/2 (100.0%) | none |
| Bet365 | 2/2 (100.0%) | none |
| Macau | 2/2 (100.0%) | none |

## AH Coverage

| Company | Coverage | Missing match_id |
|---|---|---|
| Macau | 2/2 (100.0%) | none |
| Pinnacle | 2/2 (100.0%) | none |
| Bet365 | 2/2 (100.0%) | none |
| HKJC | 2/2 (100.0%) | none |
| Crown | 2/2 (100.0%) | none |

Ladbrokes AH known missing（不自动降级）：3023474, 2910885

## OU Coverage

| Module | Coverage | Missing match_id |
|---|---|---|
| ou_dynamic_main_line | 2/2 (100.0%) | none |
| wh_ladbrokes_base_2_5 | 2/2 (100.0%) | none |
| ou_ladder | 2/2 (100.0%) | none |

## Data Integrity

- duplicate match_id：[]
- Unselected market match_id：[]
- Source-only raw/clean duplication is retained in source_tables; normalized event duplicates are reported separately.
- Excluded fixture directories：{"Matches_To_Choose": 99, "Matches_Rejected": 1353}
- Security redactions：1（位置：batch_info.redactions）

### match_id 3023474

- Health timeline：PARTIAL
- Synchronized slices：WEAK (15.9%)
- OU Ladder：COMPLETE
- Existing data QC：WARN
- Duplicate odds rows：0
- Conflicting duplicate groups：0
- Missing timeline：["1x2:europe_1x2:1017", "ah:vip:12", "ah:vip:14", "ah:vip:3", "ah:vip:35", "ah:vip:42", "ou:vip:12", "ou:vip:14", "ou:vip:3", "ou:vip:35", "ou:vip:42"]
- Company ID conflicts：0
- Cross-match contamination：0
- Odds format / impossible values：0
- Bookmaker identity issues：312
- 每条异常的 Excel sheet/row：DATA.matches.3023474.data_quality.record_issues。
- timestamp_unverified：158；示例 All_In_One:52:current, All_In_One:53:current, All_In_One:54:current
- unverified_bookmaker：312；示例 All_In_One:57:opening, All_In_One:57:current, All_In_One:58:opening

### match_id 2910885

- Health timeline：PARTIAL
- Synchronized slices：WEAK (5.8%)
- OU Ladder：COMPLETE
- Existing data QC：WARN
- Duplicate odds rows：0
- Conflicting duplicate groups：7
- Missing timeline：["1x2:europe_1x2:1017", "ah:vip:12", "ah:vip:14", "ah:vip:3", "ah:vip:35", "ah:vip:42", "ou:vip:12", "ou:vip:14", "ou:vip:3", "ou:vip:35", "ou:vip:42"]
- Company ID conflicts：0
- Cross-match contamination：0
- Odds format / impossible values：0
- Bookmaker identity issues：310
- 每条异常的 Excel sheet/row：DATA.matches.2910885.data_quality.record_issues。
- timestamp_unverified：157；示例 All_In_One:210:current, All_In_One:211:current, All_In_One:212:current
- unverified_bookmaker：310；示例 All_In_One:215:opening, All_In_One:215:current, All_In_One:216:opening

## Match Index QC

- indexed_matches：2
- alias_missing：[]
- ambiguous_teams：{}
- duplicate_fixtures：{}
- unresolved_mappings：[]
- duplicate_match_id：[]

## Source tables

| Sheet | Table | Rows |
|---|---|---|
| All_In_One | Summary | 42 |
| All_In_One | Matches_Selected | 2 |
| All_In_One | Europe_1x2 | 315 |
| All_In_One | Europe_1x2_History | 706 |
| All_In_One | Europe_1x2_History_Audit | 20 |
| All_In_One | Bookmaker_QC | 343 |
| All_In_One | Asian_Current | 30 |
| All_In_One | OverUnder_Current | 34 |
| All_In_One | OverUnder_Ladder_Clean | 82 |
| All_In_One | OverUnder_Ladder_Raw | 1131 |
| All_In_One | OU_Curve_QC | 48 |
| All_In_One | Asian_History | 551 |
| All_In_One | OverUnder_History | 456 |
| All_In_One | Asian_History_Raw | 563 |
| All_In_One | OverUnder_History_Raw | 470 |
| All_In_One | Data_Quality_Audit | 30 |
| All_In_One | H2H_Results | 20 |
| All_In_One | Home_Recent | 20 |
| All_In_One | Away_Recent | 20 |
| All_In_One | Tech_Stats | 24 |
| All_In_One | Goal_Timing | 28 |
| All_In_One | HalfFull_Stats | 18 |
| All_In_One | Goal_Distribution | 16 |
| All_In_One | Corner_Stats | 8 |
| All_In_One | Analysis_Context | 288 |
| All_In_One | Lineup_Candidate | 18 |
| All_In_One | Lineup | 2 |
| All_In_One | Odds_Candidate | 206 |
| All_In_One | Detail_Link_Candidates | 206 |
| All_In_One | Market_Fetch | 54 |
| All_In_One | Analysis_Fetch | 2 |
| All_In_One | Detail_Fetch | 2 |
| All_In_One | Fetch_Results | 6 |
| All_In_One | Matches_To_Choose | 99 |
| All_In_One | Matches_Rejected | 1353 |

## Calculation limits

- AH line_move 与同盘口 price_move 分开。
- OU HK 转 decimal 后去水；整数/四分之一盘口不当作简单二元概率。
- 未验证公司保留原始数字，排除公司比较。
- 最近报价切片包含 lookahead 标志，仅供回溯审计。
- Poisson、Bayesian、latent_total_estimate：insufficient_deterministic_input。
- DATA path：validation_packets/2026-09-05/Validation_Batch_20260905_DATA.json
- QC path：validation_packets/2026-09-05/Validation_Batch_20260905_QC.md
