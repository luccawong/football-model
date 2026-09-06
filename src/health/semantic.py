from collections import defaultdict
from datetime import datetime
from src.health.rules import HealthEvent


def _current_exists(raw, market, key):
    return any(r['quote_role'] == 'current' and r['decimal_prices'] and not r['excluded_from_calculations']
               for r in raw[market].get(key, []))


def semantic_health(matches, settings):
    cfg = settings['health']
    events = []
    per_match = {}
    total_records = total_impossible = total_conflicts = 0
    core_by_market = {'1x2': settings['core_1x2'], 'ah': settings['core_ah'], 'ou': settings['dynamic_ou']}
    ns = {'1x2': 'europe_1x2', 'ah': 'vip', 'ou': 'vip'}
    for mid, packet in matches.items():
        raw, timeline, quality = packet['raw_market'], packet['timeline'], packet['data_quality']
        records = [r for market in raw.values() for rows in market.values() for r in rows]
        total_records += len(records)
        impossible = [r for r in records if any(x in r['issues'] for x in
            ('missing_or_non_numeric','impossible_hk_value','impossible_decimal_value','unparsed_line','impossible_line'))]
        total_impossible += len(impossible)
        bad_devig = [r for r in records if r.get('devig') and abs(sum(r['devig']['probabilities'].values()) - 1) > 1e-9]
        extreme = [r for r in records if r['market_type'] == '1x2' and r.get('devig') and r['devig']['overround'] > cfg['extreme_overround']]
        if impossible:
            events.append(HealthEvent('IMPOSSIBLE_ODDS_OR_LINE', 'WARN', 'Impossible or unparseable market values found',
                (mid,), {'count': len(impossible), 'sample_record_ids': [r['record_id'] for r in impossible[:5]]}))
        if bad_devig:
            events.append(HealthEvent('DEVIG_SUM_INVALID', 'FAIL', 'De-vig probabilities do not sum to one',
                (mid,), {'count': len(bad_devig)}))
        if extreme:
            events.append(HealthEvent('EXTREME_OVERROUND', 'WARN', '1X2 overround exceeds configured limit',
                (mid,), {'count': len(extreme), 'threshold': cfg['extreme_overround']}))
        identity_failures = [r for r in records if r['identity_status'] == 'conflict']
        if identity_failures:
            core = [r for r in identity_failures if r.get('company_normalized_name') in set(sum(core_by_market.values(), []))]
            events.append(HealthEvent('CORE_BOOKMAKER_IDENTITY_CONFLICT' if core else 'BOOKMAKER_IDENTITY_CONFLICT',
                'FAIL' if core else 'WARN', 'company_id conflicts with source identity', (mid,),
                {'count': len(identity_failures), 'sample_record_ids': [r['record_id'] for r in identity_failures[:5]]}))
        contamination = [r for r in records if any(x.startswith('cross_match') for x in r['issues'])]
        if contamination:
            events.append(HealthEvent('CROSS_MATCH_CONTAMINATION', 'FAIL', 'Market row ownership does not match fixture',
                (mid,), {'count': len(contamination), 'sample_record_ids': [r['record_id'] for r in contamination[:5]]}))
        conflicting = quality.get('timestamp_collisions', [])
        total_conflicts += len(conflicting)
        if conflicting:
            events.append(HealthEvent('CONFLICTING_DUPLICATE', 'WARN', 'Same company/time/line has conflicting prices',
                (mid,), {'groups': len(conflicting), 'sample': conflicting[:5]}))
        if quality.get('source_timestamp_disorder'):
            events.append(HealthEvent('TIMELINE_SOURCE_REVERSE_ORDER', 'WARN',
                'Source history order required normalization', (mid,),
                {'groups': len(quality['source_timestamp_disorder']),
                 'company_markets': quality['source_timestamp_disorder'][:10]}))
        states = {}
        for market, names in core_by_market.items():
            for name in names:
                keys = [k for k, rows in raw[market].items() if any(r['company_normalized_name'] == name for r in rows)]
                key = keys[0] if keys else f'{ns[market]}:missing:{name}'
                rows = timeline[market].get(key, [])
                timed = [r for r in rows if r['timestamp'] and not r['excluded_from_calculations']]
                opening = any(r['quote_role'] == 'opening' for r in rows) or any(r['quote_role'] == 'opening' for r in raw[market].get(key, []))
                current = _current_exists(raw, market, key)
                gaps = []
                for a,b in zip(timed,timed[1:]):
                    gaps.append((datetime.fromisoformat(b['timestamp'])-datetime.fromisoformat(a['timestamp'])).total_seconds()/3600)
                if not timed or not current:
                    state = 'BROKEN'
                elif len(timed) < 2 or not opening:
                    state = 'PARTIAL'
                else:
                    state = 'COMPLETE'
                states[f'{market}:{name}'] = {'status': state, 'history_rows': len(rows),
                    'timestamped_rows': len(timed), 'opening_recognized': opening,
                    'current_or_frozen_recognized': current, 'max_gap_hours': max(gaps) if gaps else None,
                    'large_gap': bool(gaps and max(gaps) > cfg['large_time_gap_hours'])}
        broken = sum(v['status']=='BROKEN' for v in states.values())
        overall = 'BROKEN' if broken / len(states) >= cfg['core_timeline_broken_fail_ratio'] else \
                  'COMPLETE' if all(v['status']=='COMPLETE' for v in states.values()) else 'PARTIAL'
        if overall == 'BROKEN':
            events.append(HealthEvent('WIDESPREAD_TIMELINE_CORRUPTION', 'FAIL', 'Core bookmaker timelines are widely broken',
                (mid,), {'broken': broken, 'total': len(states)}))
        elif overall == 'PARTIAL':
            events.append(HealthEvent('PARTIAL_TIMELINE', 'WARN', 'Some core bookmaker timelines are partial',
                (mid,), {'broken': broken, 'total': len(states)}))
        slices = packet['synchronized_slices']
        aligned = sum(s['alignment_status']=='aligned' for s in slices)
        ratio = aligned/len(slices) if slices else 0
        alignment = 'STRONG' if ratio >= cfg['sync_strong_ratio'] else 'ACCEPTABLE' if ratio >= cfg['sync_acceptable_ratio'] else 'WEAK' if slices else 'UNAVAILABLE'
        if alignment in ('WEAK','UNAVAILABLE'):
            events.append(HealthEvent('SYNCHRONIZED_SLICES_WEAK', 'WARN', 'Synchronized slice alignment is weak or unavailable',
                (mid,), {'status': alignment, 'aligned': aligned, 'total': len(slices), 'ratio': ratio}))
        ladder = [r for rows in raw['ou'].values() for r in rows if r['source_table']=='OverUnder_Ladder_Clean'
                  and r['identity_status']=='verified' and r['company_normalized_name'] in settings['dynamic_ou']
                  and r['line'] is not None and r['decimal_prices']]
        company_lines = defaultdict(set)
        main, alt = 0, 0
        for r in ladder:
            company_lines[r['company_normalized_name']].add(r['line'])
            main += r['main_or_alt']=='MAIN'
            alt += r['main_or_alt']!='MAIN'
        missing_core = [name for name in settings['dynamic_ou'] if len(company_lines[name]) < cfg['ou_ladder_min_unique_lines']]
        ladder_status = 'COMPLETE' if not missing_core and main and alt else 'INCOMPLETE' if ladder else 'MISSING'
        if ladder_status != 'COMPLETE':
            events.append(HealthEvent('OU_LADDER_INCOMPLETE', 'WARN', 'OU Ladder lacks expected core line coverage',
                (mid,), {'status': ladder_status, 'missing_core': missing_core, 'main_rows': main, 'alt_rows': alt}))
        per_match[mid] = {'timeline_status': overall, 'timeline_companies': states,
            'synchronized_slice_status': alignment, 'synchronized_slice_ratio': ratio,
            'ou_ladder_status': ladder_status, 'ou_ladder_company_unique_lines': {k:len(v) for k,v in company_lines.items()},
            'semantic_counts': {'records':len(records),'impossible':len(impossible),'bad_devig':len(bad_devig),
                                'extreme_overround':len(extreme),'conflicting_duplicate_groups':len(conflicting)}}
    if total_records and total_impossible/total_records >= cfg['impossible_odds_fail_rate']:
        events.append(HealthEvent('IMPOSSIBLE_ODDS_WIDESPREAD', 'FAIL', 'Impossible market values exceed batch threshold',
            tuple(matches), {'rate':total_impossible/total_records,'threshold':cfg['impossible_odds_fail_rate']}))
    if total_records and total_conflicts/total_records >= cfg['conflicting_duplicate_fail_rate']:
        events.append(HealthEvent('CONFLICTING_DUPLICATES_WIDESPREAD', 'FAIL', 'Conflicting duplicates exceed batch threshold',
            tuple(matches), {'rate':total_conflicts/total_records,'threshold':cfg['conflicting_duplicate_fail_rate']}))
    return {'matches': per_match, 'events': events}
