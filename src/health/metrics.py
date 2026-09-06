import json
from collections import defaultdict
from pathlib import Path
from statistics import fmean
from src.health.rules import HealthEvent


def _present(packet, market, name, predicate=lambda r: True):
    return any(r['identity_status']=='verified' and r['company_normalized_name']==name and r['decimal_prices']
               and not r['excluded_from_calculations'] and predicate(r)
               for rows in packet['raw_market'][market].values() for r in rows)


def compute_metrics(matches, settings):
    n = len(matches) or 1
    coverage = {'1x2':{},'ah':{},'ou':{}}
    for name in settings['core_1x2']:
        coverage['1x2'][name] = sum(_present(p,'1x2',name) for p in matches.values())/n
    for name in settings['core_ah']:
        coverage['ah'][name] = sum(_present(p,'ah',name) for p in matches.values())/n
    for name in settings['dynamic_ou']:
        coverage['ou'][name] = sum(_present(p,'ou',name,lambda r:r['source_table']=='OverUnder_Ladder_Clean' and r['main_or_alt']=='MAIN') for p in matches.values())/n
    coverage['ou']['William Hill Base-2.5'] = sum(_present(p,'ou','William Hill',lambda r:r['line']==2.5) for p in matches.values())/n
    coverage['ou']['Ladbrokes Base-2.5'] = sum(_present(p,'ou','Ladbrokes UK',lambda r:r['line']==2.5) for p in matches.values())/n
    bookmakers, timeline_counts, ladder_counts = [], defaultdict(list), []
    unverified, total_records, duplicate_rows, missing_times, history_rows = 0, 0, 0, 0, 0
    for packet in matches.values():
        records = [r for market in packet['raw_market'].values() for rows in market.values() for r in rows]
        total_records += len(records)
        unverified += sum(r['identity_status']=='unverified' for r in records)
        duplicate_rows += len(packet['data_quality']['duplicate_issues'])
        bookmakers.append(len({r['bookmaker_key'] for r in records if r['identity_status']=='verified'}))
        for market, companies in packet['timeline'].items():
            count = sum(len(rows) for rows in companies.values())
            timeline_counts[market].append(count)
            history_rows += count
            missing_times += sum(r['timestamp'] is None for rows in companies.values() for r in rows)
        lines = defaultdict(set)
        for rows in packet['raw_market']['ou'].values():
            for r in rows:
                if r['source_table']=='OverUnder_Ladder_Clean' and r['identity_status']=='verified' and r['company_normalized_name'] in settings['dynamic_ou'] and r['line'] is not None:
                    lines[r['company_normalized_name']].add(r['line'])
        ladder_counts.extend(len(v) for v in lines.values())
    avg = lambda values: fmean(values) if values else 0
    return {'match_count':len(matches),'coverage':coverage,'average_bookmakers_per_match':avg(bookmakers),
        'average_timeline_rows_per_match':{m:avg(v) for m,v in timeline_counts.items()},
        'average_ou_ladder_unique_lines_per_core_company':avg(ladder_counts),
        'unverified_bookmaker_record_count':unverified,
        'unverified_bookmaker_record_rate':unverified/total_records if total_records else 0,
        'duplicate_row_rate':duplicate_rows/total_records if total_records else 0,
        'missing_timestamp_rate':missing_times/history_rows if history_rows else 1,
        'total_market_records':total_records}


def load_valid_history(root, current_hash, window):
    path = Path(root)/'validation_packets/history_index.json'
    entries = []
    if path.exists():
        try:
            entries = json.loads(path.read_text(encoding='utf-8')).get('batches',[])
        except (ValueError,OSError):
            return []
    results=[]
    for entry in reversed(entries):
        if entry.get('source_content_hash')==current_hash or entry.get('health_status') not in ('PASS','WARN'):
            continue
        data_path=Path(root)/entry['data_path']
        if not data_path.exists():
            continue
        try:
            data=json.loads(data_path.read_text(encoding='utf-8'))
            metrics=data.get('health',{}).get('metrics')
            if metrics:
                results.append(metrics)
        except (ValueError,OSError):
            continue
        if len(results)>=window:
            break
    return results


def _mean_baseline(history):
    if not history:
        return None
    coverage=defaultdict(lambda:defaultdict(list))
    scalar=defaultdict(list)
    timeline=defaultdict(list)
    for metrics in history:
        for market,companies in metrics['coverage'].items():
            for company,value in companies.items(): coverage[market][company].append(value)
        for key in ('average_bookmakers_per_match','average_ou_ladder_unique_lines_per_core_company',
                    'unverified_bookmaker_record_rate','duplicate_row_rate','missing_timestamp_rate'):
            scalar[key].append(metrics.get(key,0))
        for market,value in metrics.get('average_timeline_rows_per_match',{}).items():timeline[market].append(value)
    return {'coverage':{m:{c:fmean(v) for c,v in cs.items()} for m,cs in coverage.items()},
        'average_timeline_rows_per_match':{m:fmean(v) for m,v in timeline.items()},
        **{k:fmean(v) for k,v in scalar.items()},'sample_count':len(history)}


def compare_history(current, history, settings, match_ids):
    baseline=_mean_baseline(history)
    events=[]
    comparison={'baseline_available':baseline is not None,'baseline':baseline,'coverage':{}}
    if baseline is None:
        events.append(HealthEvent('HISTORICAL_BASELINE_UNAVAILABLE','INFO','No prior valid health baseline is available'))
        return comparison,events
    cfg=settings['health']
    for market,companies in current['coverage'].items():
        comparison['coverage'][market]={}
        for company,value in companies.items():
            previous=baseline.get('coverage',{}).get(market,{}).get(company)
            delta=None if previous is None else value-previous
            comparison['coverage'][market][company]={'coverage_current':value,'coverage_previous_valid_batch':previous,'coverage_delta':delta}
            if previous is None or delta >= -cfg['coverage_drop_warn']:
                continue
            fail=delta <= -cfg['coverage_drop_fail'] and previous >= cfg['coverage_collapse_previous_min']
            code='LADBROKES_1X2_COVERAGE_COLLAPSE' if market=='1x2' and company=='Ladbrokes UK' and value==0 and previous>=cfg['coverage_collapse_previous_min'] else 'COVERAGE_DROP_ALERT'
            events.append(HealthEvent(code,'FAIL' if fail or code.startswith('LADBROKES') else 'WARN',
                f'{company} {market} coverage dropped',tuple(match_ids),{'market':market,'company':company,'previous':previous,'current':value,'delta':delta}))
    monitored={'average_bookmakers_per_match':'BOOKMAKER_COUNT_DEGRADATION',
        'average_ou_ladder_unique_lines_per_core_company':'OU_LADDER_DEGRADATION'}
    for key,code in monitored.items():
        previous=baseline.get(key,0)
        current_value=current.get(key,0)
        drop=(previous-current_value)/previous if previous else 0
        if drop >= cfg['structural_drop_warn']:
            events.append(HealthEvent(code,'FAIL' if drop>=cfg['structural_drop_fail'] else 'WARN',
                f'{key} degraded relative to valid history',tuple(match_ids),{'previous':previous,'current':current_value,'relative_drop':drop}))
    for market,previous in baseline.get('average_timeline_rows_per_match',{}).items():
        current_value=current.get('average_timeline_rows_per_match',{}).get(market,0)
        drop=(previous-current_value)/previous if previous else 0
        if drop>=cfg['structural_drop_warn']:
            events.append(HealthEvent('STRUCTURAL_DEGRADATION_ALERT','FAIL' if drop>=cfg['structural_drop_fail'] else 'WARN',
                f'{market} timeline rows degraded relative to history',tuple(match_ids),{'market':market,'previous':previous,'current':current_value,'relative_drop':drop}))
    if current['missing_timestamp_rate']>=cfg['missing_timestamp_fail_rate']:
        events.append(HealthEvent('TIMESTAMP_FORMAT_OR_PARSE_FAILURE','FAIL','Missing timestamp rate exceeds failure threshold',tuple(match_ids),{'rate':current['missing_timestamp_rate']}))
    elif current['missing_timestamp_rate']>=cfg['missing_timestamp_warn_rate']:
        events.append(HealthEvent('MISSING_TIMESTAMPS_HIGH','WARN','Missing timestamp rate exceeds warning threshold',tuple(match_ids),{'rate':current['missing_timestamp_rate']}))
    return comparison,events
