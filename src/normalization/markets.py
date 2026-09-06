from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import re
from .formats import identifier, timestamp, line_value, decimal_prices
from src.bookmaker.identity import identify
from src.calculations.odds import devig
from src.timeline.slices import deduplicate

TABLES = {'Europe_1x2': '1x2', 'Europe_1x2_History': '1x2', 'Asian_Current': 'ah',
          'Asian_History': 'ah', 'OverUnder_Current': 'ou', 'OverUnder_History': 'ou',
          'OverUnder_Ladder_Clean': 'ou'}


def ownership_issues(row, match, market):
    errors = []
    mid = identifier(row.get('match_id'))
    if mid != match['match_id']:
        errors.append('cross_match_id')
    for key in ('home_team', 'away_team', 'league'):
        if row.get(key) and row[key] != match[key]:
            errors.append('cross_match_' + key)
    # OddsHistory id is data_id, not match_id. sid identifies its fixture.
    for field in ('source_url', 'detail_url'):
        url = row.get(field)
        if not url:
            continue
        parsed = urlparse(url)
        params = {k.lower(): v[0] for k, v in parse_qs(parsed.query).items()}
        expected_mid = params.get('sid') if 'oddshistory' in parsed.path.lower() else params.get('id')
        if expected_mid and expected_mid != mid:
            errors.append('cross_match_url')
        path_id = re.search(r'/(\d+)(?:cn|sb)?\.(?:js|htm)', parsed.path)
        if path_id and path_id[1] != mid:
            errors.append('cross_match_url')
        url_company = params.get('companyid') or params.get('cid')
        if url_company and url_company != identifier(row.get('company_id')):
            errors.append('company_id_url_conflict')
        if 'oddshistory' in parsed.path.lower() and row.get('data_id') and params.get('id') != identifier(row['data_id']):
            errors.append('company_data_id_url_conflict')
    return sorted(set(errors))


def normalize_row(row, table, role, match, mapping, settings, anchor):
    market = TABLES[table]
    identity = identify(row, market, mapping)
    src = row['_source']
    issues = ownership_issues(row, match, market) + identity['identity_issues']
    raw_time, offset, time_basis = None, settings['history_timezone_offset_hours'], None
    if table.endswith('History'):
        raw_time = row.get('change_time')
        time_basis = 'source_history_Asia/Shanghai; year nearest source anchor if absent'
    elif table == 'Europe_1x2' and role == 'current':
        raw_time = row.get('update_time')
        offset = settings['europe_update_timezone_offset_hours']
        time_basis = 'update_time timezone unverified' if offset is None else 'configured update_time offset'
    elif table == 'OverUnder_Ladder_Clean' and role == 'current':
        raw_time = row.get('observed_at_utc')
        time_basis = 'snapshot_observed_at; not quote-change time'
    ts = timestamp(raw_time, anchor, offset)
    if raw_time and not ts:
        issues.append('timestamp_unverified')
    if market == '1x2':
        labels, fmt, line, line_raw = ['home', 'draw', 'away'], 'DECIMAL', None, None
        prices = [row.get(k) for k in (['home_odds', 'draw_odds', 'away_odds'] if table.endswith('History')
                                      else [f'{"initial" if role == "opening" else "current"}_{x}' for x in labels])]
        fmt_basis = 'Titan 1X2 decimal columns'
    else:
        labels = ['home', 'away'] if market == 'ah' else ['over', 'under']
        fmt, fmt_basis = settings['vip_odds_format'], settings['vip_odds_format_basis']
        if table.endswith('History'):
            prices, line_raw = [row.get('left_water'), row.get('right_water')], row.get('market_line')
        elif table == 'OverUnder_Ladder_Clean':
            prices = [row.get(role + '_over_raw'), row.get(role + '_under_raw')]
            line_raw = row.get(role + '_line_raw')
            fmt = row.get(role + '_odds_format') or 'UNKNOWN'
            fmt_basis = 'source declared ladder format; crawler heuristic, independently checked for valid prices'
        else:
            prefix = 'initial' if role == 'opening' else 'current'
            prices = [row.get(prefix + '_left'), row.get(prefix + '_right')]
            line_raw = row.get(prefix + '_line')
        line = line_value(line_raw, market)
        if line is None:
            issues.append('unparsed_line')
        elif (market == 'ou' and line < 0) or abs(line * 4 - round(line * 4)) > 1e-8:
            issues.append('impossible_line')
    decimal, error = decimal_prices(prices, fmt, settings['max_decimal_odds'])
    if error:
        issues.append(error)
    if ts and datetime.fromisoformat(ts) > datetime.fromisoformat(anchor):
        issues.append('timestamp_after_crawler')
    # Preserve every raw input but never calculate on contaminated/conflicting records.
    excluded = bool([e for e in issues if e != 'timestamp_unverified']) or identity['identity_status'] != 'verified'
    is_opening = bool(row.get('is_opening')) if market == '1x2' and table.endswith('History') else False
    if table.endswith('History') and row.get('Record_Type') not in (None, 'HISTORY_EVENT'):
        excluded = True
        issues.append('not_record_level_history')
    record = dict(match_id=match['match_id'], **identity, market_type=market, timestamp=ts,
        timestamp_raw=raw_time, timestamp_basis=time_basis, line=line, line_raw=line_raw,
        prices=prices, decimal_prices=decimal, odds_format=fmt, odds_format_basis=fmt_basis,
        home_price=prices[0] if market != 'ou' else None,
        draw_price=prices[1] if market == '1x2' else None,
        away_price=prices[-1] if market != 'ou' else None,
        over_price=prices[0] if market == 'ou' else None, under_price=prices[-1] if market == 'ou' else None,
        main_or_alt=row.get('line_type') or row.get('Line_Type') or ('MAIN' if market != '1x2' else None),
        quote_role=('opening' if is_opening else role), opening_verification='source_flag_only' if is_opening or role == 'opening' else None,
        lifecycle_status=('frozen' if match['status'] == 'finished' else role),
        raw_text=row.get('raw_text') or row.get('raw'), **src,
        record_id=f"{src['source_sheet']}:{src['source_row']}:{role}",
        issues=sorted(set(issues)), excluded_from_calculations=excluded,
        devig=devig(decimal, labels) if decimal and not excluded else None,
        raw_fields=row)
    return record


def build_markets(tables, match, mapping, settings, anchor):
    raw = {m: defaultdict(list) for m in ('1x2', 'ah', 'ou')}
    timelines = {m: defaultdict(list) for m in ('1x2', 'ah', 'ou')}
    records, duplicates = [], []
    mid = match['match_id']
    for table, market in TABLES.items():
        for row in tables.get(table, []):
            if identifier(row.get('match_id')) != mid:
                continue
            roles = ['history'] if table.endswith('History') else ['opening', 'current']
            for role in roles:
                record = normalize_row(row, table, role, match, mapping, settings, anchor)
                key = record['bookmaker_key'] or 'unverified:' + record['record_id']
                raw[market][key].append(record)
                records.append(record)
                if table.endswith('History'):
                    timelines[market][key].append(record)
    for market, companies in timelines.items():
        for key, rows in companies.items():
            companies[key], removed = deduplicate(rows)
            duplicates.extend(dict(market=market, bookmaker_key=key, **r) for r in removed)
    return {k: dict(v) for k,v in raw.items()}, {k: dict(v) for k,v in timelines.items()}, records, duplicates
