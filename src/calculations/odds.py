from itertools import combinations


def devig(prices, labels):
    implied = [1 / p for p in prices]
    total = sum(implied)
    return {'raw_implied': dict(zip(labels, implied)), 'overround': total - 1,
            'probabilities': dict(zip(labels, [p / total for p in implied]))}


def differences(companies):
    result = []
    for (ak, a), (bk, b) in combinations(sorted(companies.items()), 2):
        if not a.get('devig') or not b.get('devig'):
            continue
        result.append({'company_a': ak, 'company_b': bk,
                       'percentage_point_difference_a_minus_b': {
                           k: 100 * (v - b['devig']['probabilities'][k])
                           for k, v in a['devig']['probabilities'].items()}})
    return result


def movements(rows):
    changes = []
    for a, b in zip(rows, rows[1:]):
        if a['line'] is None or b['line'] is None:
            continue
        if a['line'] != b['line']:
            changes.append(dict(kind='line_move', from_line=a['line'], to_line=b['line'],
                                from_record_id=a['record_id'], to_record_id=b['record_id']))
        elif a['prices'] != b['prices']:
            changes.append(dict(kind='price_move', line=b['line'], from_prices=a['prices'], to_prices=b['prices'],
                                from_record_id=a['record_id'], to_record_id=b['record_id']))
    return changes
