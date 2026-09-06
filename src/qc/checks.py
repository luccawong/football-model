from collections import Counter, defaultdict
from datetime import datetime


def coverage(records, names, market):
    return {name: ('present' if any(r['market_type'] == market and r['company_normalized_name'] == name
                and r['identity_status'] == 'verified' and not r['excluded_from_calculations'] and r['decimal_prices']
                for r in records) else 'missing') for name in names}


def quality(records, timeline, slices, duplicates, settings):
    warnings, failures = [], []
    issues = defaultdict(list)
    for r in records:
        for issue in r['issues']:
            issues[issue].append(r['record_id'])
        if r['identity_status'] == 'unverified':
            issues['unverified_bookmaker'].append(r['record_id'])
    for name, rows in issues.items():
        warnings.append(name)
        if name.startswith('cross_match') or name.startswith('company_id_') or name == 'company_data_id_url_conflict':
            failures.append(name)
    cov1 = coverage(records, settings['core_1x2'], '1x2')
    covah = coverage(records, settings['core_ah'], 'ah')
    for market, cov in [('1x2', cov1), ('ah', covah)]:
        warnings += [f'missing_{market}:{name}' for name, state in cov.items() if state == 'missing']
    ladah = coverage(records, ['Ladbrokes UK'], 'ah')['Ladbrokes UK']
    missing_timeline = []
    completeness, disorders, collisions = {}, [], []
    for market in ('1x2', 'ah', 'ou'):
        selected = [r for r in records if r['market_type'] == market and r['identity_status'] == 'verified']
        keys = sorted({r['bookmaker_key'] for r in selected})
        for key in keys:
            rows = timeline[market].get(key, [])
            timed = [r for r in rows if r['timestamp']]
            opening = [r for r in rows if r['quote_role'] == 'opening']
            # Source-only opening with no timestamp does not prove complete lifecycle.
            completeness[f'{market}:{key}'] = dict(history_rows=len(rows), timestamped_rows=len(timed),
                source_opening_flag_present=bool(opening), status='available_not_proven_complete' if timed else 'missing',
                true_opening_verified=False)
            if not timed:
                missing_timeline.append(f'{market}:{key}')
            source_order = sorted(timed, key=lambda r: r['source_row'])
            if [r['timestamp'] for r in source_order] != sorted(r['timestamp'] for r in source_order):
                disorders.append(f'{market}:{key}')
            at_time = defaultdict(set)
            for r in timed:
                at_time[(r['timestamp'], r['line'])].add(tuple(r['prices']))
            collisions += [dict(market=market, bookmaker_key=key, timestamp=t, line=line, distinct_quotes=len(values))
                           for (t,line), values in at_time.items() if len(values)>1]
    if missing_timeline:
        warnings.append('missing_timeline')
    if collisions:
        warnings.append('timestamp_collisions')
    if any(s['alignment_status'] == 'weak_alignment' for s in slices):
        warnings.append('weak_synchronized_slices')
    valid = sum(bool(r['devig']) for r in records)
    if not valid:
        failures.append('no_valid_quotes')
    return dict(overall_status='FAIL' if failures else 'WARN' if warnings else 'PASS', minimum_qc_passed=not failures,
        warnings=sorted(set(warnings)), failures=sorted(set(failures)), valid_quote_count=valid,
        core_1x2=cov1, core_ah=covah,
        ladbrokes_ah=dict(status='available' if ladah=='present' else 'unavailable',
            reason='verified source quotes present' if ladah=='present' else 'current Titan crawler/source does not provide verified Ladbrokes AH',
            confidence_penalty='none_by_default'),
        record_issues=dict(issues), duplicate_issues=duplicates, timeline_statistics=completeness,
        source_timestamp_disorder=disorders, timestamp_collisions=collisions, missing_timeline=missing_timeline,
        timeline_complete_status='UNKNOWN',
        synchronized_slice_count=len(slices), aligned_slice_count=sum(s['alignment_status']=='aligned' for s in slices))


def index_qc(index):
    teams, fixtures = defaultdict(set), defaultdict(set)
    for row in index:
        for name in row['home_aliases'] + row['away_aliases']:
            teams[name.casefold()].add(row['match_id'])
        fixtures[(row['home_team'],row['away_team'])].add(row['match_id'])
    return dict(indexed_matches=len(index), alias_missing=[r['match_id'] for r in index if not r['home_aliases'] or not r['away_aliases']],
        ambiguous_teams={k: sorted(v) for k,v in teams.items() if len(v)>1},
        duplicate_fixtures={' vs '.join(k):sorted(v) for k,v in fixtures.items() if len(v)>1},
        unresolved_mappings=[r['match_id'] for r in index if r['unresolved_team_mapping']],
        duplicate_match_id=[k for k,v in Counter(r['match_id'] for r in index).items() if v>1])


def validate_packet(data):
    from jsonschema import Draft202012Validator
    schema = {'type':'object','required':['schema_version','batch_info','match_index','matches'],
        'properties': {'schema_version': {'const':'1.0'}, 'matches': {'type':'object','minProperties':1,
            'patternProperties': {'^[0-9]+$': {'type':'object','required':['match_identity','data_quality','raw_market','timeline','synchronized_slices','context','calculations']}},
            'additionalProperties': False}, 'match_index': {'type':'array'}}}
    Draft202012Validator(schema).validate(data)
    ids = set(data['matches'])
    if ids != {r['match_id'] for r in data['match_index']} or len(ids) != len(data['match_index']):
        raise ValueError('Index IDs do not match packet IDs')
    if data['batch_info']['match_count'] != len(ids):
        raise ValueError('Batch count mismatch')
    for mid, packet in data['matches'].items():
        if packet['match_identity']['match_id'] != mid:
            raise ValueError('Cross-match identity contamination')
        for market in packet['raw_market'].values():
            for rows in market.values():
                for r in rows:
                    if r['match_id'] != mid:
                        raise ValueError('Cross-match quote contamination')
                    if r['devig'] and abs(sum(r['devig']['probabilities'].values())-1)>1e-12:
                        raise ValueError('Invalid probability sum')
        for companies in packet['timeline'].values():
            for rows in companies.values():
                times = [r['timestamp'] for r in rows if r['timestamp']]
                if times != sorted(times):
                    raise ValueError('Unsorted normalized timeline')
    forbidden = {'codex_analysis','H1','H2','h1','h2','main_pick','non_main_pick','red_team_verdict','final_view'}
    def visit(obj):
        if isinstance(obj,dict):
            if forbidden.intersection(obj):
                raise ValueError('Analysis field in DATA')
            for v in obj.values(): visit(v)
        elif isinstance(obj,list):
            for v in obj: visit(v)
    visit(data)
