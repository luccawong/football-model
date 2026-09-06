from datetime import datetime
from src.calculations.odds import differences


def deduplicate(rows):
    seen, unique, duplicates = {}, [], []
    for row in rows:
        key = (row['match_id'], row['bookmaker_key'], row['market_type'], row['timestamp'],
               row['line'], tuple(row['prices']), row['odds_format'], row['main_or_alt'], row['quote_role'])
        # Unknown identity/time cannot safely collapse independent source records.
        if row['timestamp'] is None or row['bookmaker_key'] is None:
            unique.append(row)
        elif key in seen:
            duplicates.append({'kept': seen[key], 'duplicate': row['record_id']})
        else:
            seen[key] = row['record_id']
            unique.append(row)
    return sorted(unique, key=lambda x: (x['timestamp'] is None, x['timestamp'] or '', x['record_id'])), duplicates


def synchronize(histories, settings):
    valid = {k: [r for r in v if r['timestamp'] and r.get('devig') and r['identity_status'] == 'verified'
                 and r['company_normalized_name'] in settings['core_1x2'] and not r.get('excluded_from_calculations')]
             for k, v in histories.items()}
    valid = {k: v for k, v in valid.items() if v}
    targets = sorted({r['timestamp'] for rows in valid.values() for r in rows})
    result = []
    for target in targets:
        t = datetime.fromisoformat(target)
        companies = {}
        for key, rows in valid.items():
            nearest = min(rows, key=lambda r: (abs((datetime.fromisoformat(r['timestamp']) - t).total_seconds()),
                                               r['timestamp'] > target, r['record_id']))
            gap = abs((datetime.fromisoformat(nearest['timestamp']) - t).total_seconds()) / 60
            companies[key] = dict(company=nearest['company_normalized_name'], company_id=nearest['company_id'],
                                  source_timestamp=nearest['timestamp'], source_record_id=nearest['record_id'],
                                  time_gap_minutes=gap, lookahead=nearest['timestamp'] > target,
                                  odds=nearest['prices'], devig=nearest['devig'],
                                  alignment_status='aligned' if gap <= settings['alignment_max_gap_minutes'] else 'weak_alignment')
        aligned = {k: v for k, v in companies.items() if v['alignment_status'] == 'aligned'}
        result.append(dict(target_time=target, max_time_gap_minutes=settings['alignment_max_gap_minutes'],
                           alignment_status='aligned' if len(aligned) >= settings['alignment_min_companies'] and len(aligned) == len(companies) else 'weak_alignment',
                           missing_core_companies=sorted(set(settings['core_1x2']) - {v['company'] for v in companies.values()}),
                           companies=companies, probability_differences=differences(aligned),
                           usage='retrospective_nearest_quotes; lookahead explicitly flagged; not a backtest signal'))
    return result
