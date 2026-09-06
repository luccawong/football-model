from src.normalization.formats import identifier


def identify(row, market, mapping):
    ns = 'europe_1x2' if market == '1x2' else 'vip'
    cid = identifier(row.get('company_id'))
    key = f'{ns}:{cid}' if cid else None
    raw = row.get('company_raw') or row.get('company_en') or row.get('company')
    meta = mapping.get(key, {})
    verified = bool(meta.get('verified'))
    normalized = meta.get('normalized_name') if verified else None
    issues = []
    claimed_key = row.get('bookmaker_key')
    if claimed_key and claimed_key != (key or f'{ns}:NO_ID'):
        issues.append('company_id_key_conflict')
    claimed_name = row.get('company_canonical')
    if verified and claimed_name and claimed_name not in (normalized, 'UNKNOWN_COMPANY_ID'):
        issues.append('company_id_name_conflict')
    # Explicit full-name contradictions matter even if canonical metadata was copied.
    for other_key, other in mapping.items():
        if other_key.startswith(ns + ':') and other.get('verified') and raw in other.get('full_names', []):
            if other['normalized_name'] != normalized and verified:
                issues.append('company_id_raw_name_conflict')
    return dict(company_id=cid, company_raw_name=raw, company_normalized_name=normalized,
                bookmaker_key=key, identity_status='conflict' if issues else ('verified' if verified else 'unverified'),
                identity_issues=sorted(set(issues)))
