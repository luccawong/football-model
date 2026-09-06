from collections import Counter
from src.health.rules import HealthEvent


def _compatible(observed, expected):
    if observed == 'integer' and 'number' in expected:
        return True
    if observed == 'integer' and 'numeric_string' in expected:
        return True
    if observed == 'numeric_string' and 'string' in expected:
        return True
    return observed in expected


def detect_schema(tables, inventory, fingerprint, bookmaker_mapping):
    events = []
    actual = {item['table']: item for item in inventory}
    for name, spec in fingerprint['tables'].items():
        tier = spec['tier']
        severity = 'FAIL' if tier == 'CRITICAL' else 'WARN' if tier == 'IMPORTANT' else 'INFO'
        item = actual.get(name)
        if item is None:
            events.append(HealthEvent(f'{tier}_SHEET_MISSING', severity,
                f'{name} is absent from the workbook', details={'table': name, 'tier': tier}))
            continue
        columns = set(item.get('columns', []))
        for required in spec['required_columns']:
            if required not in columns:
                aliases = [a for a in spec.get('known_aliases', {}).get(required, []) if a in columns]
                code = 'REQUIRED_COLUMN_RENAMED' if aliases else 'REQUIRED_COLUMN_MISSING'
                events.append(HealthEvent(code, severity, f'{name}.{required} is missing',
                    details={'table': name, 'column': required, 'observed_aliases': aliases, 'tier': tier}))
        known = set(spec['required_columns']) | set(spec.get('optional_columns', []))
        unknown = sorted(columns - known)
        if unknown:
            events.append(HealthEvent('UNKNOWN_COLUMNS_ADDED', 'INFO', f'{name} has additional columns',
                details={'table': name, 'columns': unknown}))
        rows = tables.get(name, [])
        for key, nullable in spec.get('nullable_policy', {}).items():
            if nullable is False and key in columns and (not rows or all(r.get(key) in (None, '') for r in rows)):
                events.append(HealthEvent('REQUIRED_KEY_ALL_NULL', severity, f'{name}.{key} is all null',
                    details={'table': name, 'column': key, 'tier': tier}))
        for column, expected in spec.get('expected_dtypes', {}).items():
            counts = item.get('observed_dtypes', {}).get(column, {})
            non_null = {kind: count for kind, count in counts.items() if kind != 'null'}
            total = sum(non_null.values())
            bad = sum(count for kind, count in non_null.items() if not _compatible(kind, expected))
            if total and bad / total >= 0.20:
                events.append(HealthEvent('CRITICAL_COLUMN_TYPE_CHANGE' if tier == 'CRITICAL' else 'COLUMN_TYPE_CHANGE',
                    severity, f'{name}.{column} type changed', details={'table': name, 'column': column,
                    'expected': expected, 'observed': non_null, 'bad_rate': bad / total, 'tier': tier}))
        unique = spec.get('unique_key_fields')
        if unique and rows:
            keys = [tuple(r.get(k) for k in unique) for r in rows]
            duplicate_rows = sum(v - 1 for v in Counter(keys).values() if v > 1)
            if duplicate_rows:
                events.append(HealthEvent('DUPLICATE_KEY_EXPLOSION', severity,
                    f'{name} unique key is duplicated', details={'table': name, 'key_fields': unique,
                    'duplicate_rows': duplicate_rows, 'row_count': len(rows), 'tier': tier}))
    protected = fingerprint.get('protected_bookmaker_identities', {})
    for key, expected in protected.items():
        meta = bookmaker_mapping.get(key)
        if not meta or not meta.get('verified') or meta.get('normalized_name') != expected:
            code = 'BET365_IDENTITY_POLLUTION' if expected == 'Bet365' else 'CORE_BOOKMAKER_IDENTITY_CONFLICT'
            events.append(HealthEvent(code, 'FAIL', f'Protected bookmaker mapping changed for {key}',
                details={'bookmaker_key': key, 'expected': expected, 'observed': meta}))
    for key, meta in bookmaker_mapping.items():
        if meta.get('verified') and meta.get('normalized_name','').startswith('Ladbrokes') and '利*' in meta.get('raw_name', []):
            events.append(HealthEvent('MASKED_NAME_MAPPED_TO_LADBROKES', 'FAIL',
                'Masked 利* must not be mapped to Ladbrokes', details={'bookmaker_key': key}))
        if meta.get('verified') and meta.get('normalized_name') == 'Bet365' and 'PlanetWin365' in meta.get('raw_name', []):
            events.append(HealthEvent('BET365_IDENTITY_POLLUTION', 'FAIL',
                'PlanetWin365 must not be mapped to Bet365', details={'bookmaker_key': key}))
    return {'fingerprint_version': fingerprint['fingerprint_version'],
            'schema_drift': any(e.code not in ('UNKNOWN_COLUMNS_ADDED',) for e in events),
            'events': events,
            'tables_checked': len(fingerprint['tables']),
            'tables_observed': len(actual)}
