import json


def report(data):
    info, matches, health = data['batch_info'], data['matches'], data['health']
    n, status = info['match_count'], health['status']
    schema_text = 'DETECTED' if health['schema_drift'] else 'NONE'
    latest = 'NO' if status == 'FAIL' else 'YES (after local acceptance)'
    lines = ['# Batch Health', '', f'STATUS: {status}', '',
        f'Matches: {len(matches)}/{n}', f'Schema drift: {schema_text}',
        f'Critical errors: {health["critical_error_count"]}', f'Warnings: {health["warning_count"]}',
        f'Latest update: {latest}', f'Git push: {"VALID BATCH NOT CHANGED" if status=="FAIL" else "PENDING AFTER QC"}', '',
        'Core 1X2 coverage:']
    for company,value in health.get('coverage_current',{}).get('1x2',{}).items():
        lines.append(f'{company}: {round(value*n)}/{n}')
    complete_ladders = sum(p.get('health',{}).get('ou_ladder_status')=='COMPLETE' for p in matches.values())
    lines += ['', 'AH Ladbrokes:', 'KNOWN_EXCEPTION', '', 'OU Ladder:',
              f'{complete_ladders}/{len(matches)} complete' if matches else '0/0 complete']
    if status == 'FAIL':
        lines += ['', 'Reason:'] + health['reason_codes'] + ['', 'latest.json updated: NO',
            'Git push valid batch: NO', '', 'Failed batch saved under: failed_batches/' + info['batch_date'] + '/']
    lines += ['', '## Health events', '', '| Severity | Code | match_id | Details |', '|---|---|---|---|']
    for event in health['events']:
        details=json.dumps(event.get('details',{}),ensure_ascii=False,separators=(',',':'))
        lines.append(f"| {event['severity']} | {event['code']} | {', '.join(event.get('match_ids',[])) or 'batch'} | {details} |")
    schema=health.get('schema',{})
    lines += ['', '## Schema fingerprint', '', f'- Version：{schema.get("fingerprint_version")}',
        f'- Tables checked：{schema.get("tables_checked")}', f'- Tables observed：{schema.get("tables_observed")}',
        f'- Schema drift：{schema_text}', '', '## Coverage monitor', '',
        '| Market | Company | Current | Previous valid baseline | Delta |', '|---|---|---:|---:|---:|']
    comparison=health.get('historical_comparison',{}).get('coverage',{})
    for market,companies in health.get('coverage_current',{}).items():
        for company,current in companies.items():
            entry=comparison.get(market,{}).get(company,{})
            previous,delta=entry.get('coverage_previous_valid_batch'),entry.get('coverage_delta')
            fmt=lambda v:'N/A' if v is None else f'{v:.1%}'
            lines.append(f'| {market} | {company} | {fmt(current)} | {fmt(previous)} | {fmt(delta)} |')
    metrics=health.get('metrics',{})
    baseline=health.get('historical_comparison',{}).get('baseline') or {}
    lines += ['', '## Historical health baseline', '',
        f'- Baseline available：{health.get("historical_comparison",{}).get("baseline_available",False)}',
        f'- Baseline sample count：{baseline.get("sample_count",0)}',
        f'- Average bookmakers/match：{metrics.get("average_bookmakers_per_match","N/A")}',
        f'- Average timeline rows/match：{json.dumps(metrics.get("average_timeline_rows_per_match",{}),ensure_ascii=False)}',
        f'- Average core OU Ladder lines/company：{metrics.get("average_ou_ladder_unique_lines_per_core_company","N/A")}',
        f'- Unverified bookmaker row rate：{metrics.get("unverified_bookmaker_record_rate","N/A")}',
        f'- Duplicate row rate：{metrics.get("duplicate_row_rate","N/A")}',
        f'- Missing timestamp rate (history)：{metrics.get("missing_timestamp_rate","N/A")}',
        '', '## 比赛索引', '', '| match_id | league | fixture | kickoff | status |', '|---|---|---|---|---|']
    for row in data['match_index']:
        lines.append(f"| {row['match_id']} | {row['league']} | {row['home_team']} vs {row['away_team']} | {row['kickoff_time']} | {row['status']} |")
    for title, field in [('1X2 Coverage','core_1x2'),('AH Coverage','core_ah')]:
        lines += ['', f'## {title}', '', '| Company | Coverage | Missing match_id |','|---|---|---|']
        names = list(next(iter(matches.values()))['data_quality'][field]) if matches else []
        for name in names:
            missing = [mid for mid,p in matches.items() if p['data_quality'][field][name]=='missing']
            lines.append(f"| {name} | {n-len(missing)}/{n} ({(n-len(missing))/n:.1%}) | {', '.join(missing) or 'none'} |")
    if matches:
        lines += ['', 'Ladbrokes AH known missing（不自动降级）：' + ', '.join(mid for mid,p in matches.items() if p['data_quality']['ladbrokes_ah']['status']=='unavailable'),
                  '', '## OU Coverage', '', '| Module | Coverage | Missing match_id |', '|---|---|---|']
        for field in ['ou_dynamic_main_line','wh_ladbrokes_base_2_5','ou_ladder']:
            missing = [mid for mid,p in matches.items() if not p['calculations'][field]]
            lines.append(f"| {field} | {n-len(missing)}/{n} ({(n-len(missing))/n:.1%}) | {', '.join(missing) or 'none'} |")
    lines += ['', '## Data Integrity', '', f'- duplicate match_id：{data["batch_qc"].get("duplicate_match_ids",[])}',
        f'- Unselected market match_id：{data["batch_qc"].get("unselected_market_match_ids",[])}',
        '- Source-only raw/clean duplication is retained in source_tables; normalized event duplicates are reported separately.',
        f'- Excluded fixture directories：{json.dumps(info["excluded_catalog_counts"],ensure_ascii=False)}',
        f'- Security redactions：{len(info["redactions"])}（位置：batch_info.redactions）']
    for mid,p in matches.items():
        q, mh = p['data_quality'], p['health']
        lines += ['', f'### match_id {mid}', '', f'- Health timeline：{mh["timeline_status"]}',
            f'- Synchronized slices：{mh["synchronized_slice_status"]} ({mh["synchronized_slice_ratio"]:.1%})',
            f'- OU Ladder：{mh["ou_ladder_status"]}', f'- Existing data QC：{q["overall_status"]}',
            f'- Duplicate odds rows：{len(q["duplicate_issues"])}', f'- Conflicting duplicate groups：{len(q["timestamp_collisions"])}',
            f'- Missing timeline：{json.dumps(q["missing_timeline"],ensure_ascii=False)}',
            f'- Company ID conflicts：{sum(len(v) for k,v in q["record_issues"].items() if k.startswith("company_"))}',
            f'- Cross-match contamination：{sum(len(v) for k,v in q["record_issues"].items() if k.startswith("cross_match"))}',
            f'- Odds format / impossible values：{sum(len(v) for k,v in q["record_issues"].items() if any(s in k for s in ("odds_format","impossible","non_numeric")))}',
            f'- Bookmaker identity issues：{len(q["record_issues"].get("unverified_bookmaker",[]))}',
            '- 每条异常的 Excel sheet/row：DATA.matches.' + mid + '.data_quality.record_issues。']
        for issue,refs in sorted(q['record_issues'].items()):
            lines.append(f'- {issue}：{len(refs)}；示例 {", ".join(refs[:3])}')
    lines += ['', '## Match Index QC', '']
    for key,value in data['batch_qc'].get('match_index_qc',{}).items():
        lines.append(f'- {key}：{json.dumps(value,ensure_ascii=False)}')
    lines += ['', '## Source tables', '', '| Sheet | Table | Rows |', '|---|---|---|']
    for item in info['table_inventory']:
        lines.append(f"| {item['sheet']} | {item['table']} | {item['rows']} |")
    lines += ['', '## Calculation limits', '', '- AH line_move 与同盘口 price_move 分开。',
        '- OU HK 转 decimal 后去水；整数/四分之一盘口不当作简单二元概率。',
        '- 未验证公司保留原始数字，排除公司比较。', '- 最近报价切片包含 lookahead 标志，仅供回溯审计。',
        '- Poisson、Bayesian、latent_total_estimate：insufficient_deterministic_input。',
        f'- DATA path：{info["data_path"]}', f'- QC path：{info["qc_path"]}', '']
    return '\n'.join(lines)
