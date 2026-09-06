import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from src.parser.titan import read_tables
from src.normalization.formats import identifier, timestamp
from src.normalization.markets import build_markets, TABLES
from src.calculations.odds import differences, movements
from src.timeline.slices import synchronize
from src.index.match_index_builder import build_index
from src.qc.checks import quality, index_qc, validate_packet
from src.qc.report import report
from src.export.files import content_hash, publish_files, publish_failed, unchanged
from src.export.security import sanitize
from src.health.schema import detect_schema
from src.health.semantic import semantic_health
from src.health.metrics import compute_metrics, load_valid_history, compare_history
from src.health.rules import HealthEvent, RuleEngine


def read_config(root):
    return [json.loads((root / 'config' / name).read_text(encoding='utf-8'))
            for name in ('settings.json', 'bookmaker_mapping.json', 'team_aliases.json', 'schema_fingerprint.json')]


def calculate(raw, timelines, slices, settings):
    records = [r for market in raw.values() for rows in market.values() for r in rows]
    valid = [r for r in records if r['devig']]
    one = [r for r in valid if r['market_type'] == '1x2']
    quote_ref = lambda r: dict(record_id=r['record_id'], bookmaker_key=r['bookmaker_key'],
                               timestamp=r['timestamp'], line=r['line'], odds=r['prices'], devig=r['devig'])
    snapshot = {k: next((r for r in rows if r['quote_role']=='current' and r['devig']), None)
                for k,rows in raw['1x2'].items()}
    snapshot = {k:r for k,r in snapshot.items() if r and r['company_normalized_name'] in settings['core_1x2']}
    changes = []
    for key, rows in raw['1x2'].items():
        opening = next((r for r in rows if r['source_table']=='Europe_1x2' and r['quote_role']=='opening' and r['devig']), None)
        current = next((r for r in rows if r['source_table']=='Europe_1x2' and r['quote_role']=='current' and r['devig']), None)
        if opening and current:
            changes.append(dict(bookmaker_key=key, opening_record_id=opening['record_id'], current_record_id=current['record_id'],
                opening_time=opening['timestamp'], current_time=current['timestamp'],
                anchor_status='source_reported_opening; true first market quote unverified',
                percentage_point_change={k:100*(v-opening['devig']['probabilities'][k]) for k,v in current['devig']['probabilities'].items()}))
    ah = {}
    for key, rows in raw['ah'].items():
        anchor = {role: next((quote_ref(r) for r in rows if r['source_table']=='Asian_Current' and r['quote_role']==role), None)
                  for role in ('opening','current')}
        anchor['movements'] = movements([r for r in timelines['ah'].get(key,[]) if r['timestamp'] and r['devig']])
        ah[key] = anchor
    ou = [r for r in valid if r['market_type']=='ou']
    ladder = [quote_ref(r) | dict(quote_role=r['quote_role'], main_or_alt=r['main_or_alt'],
              probability_semantics='binary_over_under' if r['line'] is not None and r['line'] % 1 == .5 else 'settlement_weighted_price_not_binary_probability')
              for r in ou if r['source_table']=='OverUnder_Ladder_Clean']
    # All clean ladder rows, including unverified and invalid ones, remain in raw_market and source_tables.
    return dict(devig_1x2=[quote_ref(r) for r in one], opening_current_probability_change=changes,
        company_probability_differences=dict(current_snapshot=dict(status='not_time_aligned_do_not_treat_as_simultaneous',
            quotes={k:quote_ref(r) for k,r in snapshot.items()}, differences=differences(snapshot)),
            same_time_slice=[dict(target_time=s['target_time'], alignment_status=s['alignment_status'], differences=s['probability_differences']) for s in slices]),
        ah_repricing=ah,
        ou_dynamic_main_line=[quote_ref(r) | dict(quote_role=r['quote_role']) for r in ou
            if r['company_normalized_name'] in settings['dynamic_ou'] and r['main_or_alt']=='MAIN' and r['source_table']=='OverUnder_Ladder_Clean'],
        ou_ladder=ladder,
        wh_ladbrokes_base_2_5=[quote_ref(r) | dict(quote_role=r['quote_role'], persistent_fixed_line='unverified') for r in ou
            if r['company_normalized_name'] in ('William Hill','Ladbrokes UK') and r['line']==2.5],
        latent_total_estimate=dict(status='insufficient_deterministic_input',reason='No configured settlement-aware distribution fitting model'),
        poisson=dict(status='insufficient_deterministic_input'), bayesian_score=dict(status='insufficient_deterministic_input'))


def build(excel_path, root):
    root, excel_path = Path(root), Path(excel_path)
    settings, mapping, aliases, fingerprint = read_config(root)
    tables, inventory = read_tables(excel_path)
    # Content hash uses cell data, not volatile ZIP timestamps.
    cell_hash = content_hash(tables)
    redactions = []
    tables = sanitize(tables, redactions)
    summary = {r['metric']:r.get('value') for r in tables.get('Summary',[])}
    utc_times = [r.get('scraped_at_utc') or r.get('observed_at_utc') for r in tables.get('OverUnder_Ladder_Clean',[])]
    utc_times = [timestamp(t, '2000-01-01T00:00:00+00:00', None) for t in utc_times if t]
    utc_times = [t for t in utc_times if t]
    run_time = str(summary.get('run_time') or '')
    # Prefer explicit UTC source observations. Filename is never required.
    crawler_timestamp = max(utc_times) if utc_times else None
    crawler_timestamp_basis = 'latest explicit UTC ladder scrape timestamp; Summary.run_time retained separately'
    if not crawler_timestamp and run_time:
        try:
            local = datetime.fromisoformat(run_time).replace(tzinfo=ZoneInfo(settings['summary_run_time_timezone']))
            crawler_timestamp = local.astimezone(timezone.utc).isoformat(timespec='seconds')
            crawler_timestamp_basis = 'Summary.run_time using configured crawler timezone ' + settings['summary_run_time_timezone']
        except (ValueError,KeyError):
            pass
    if not crawler_timestamp:
        # Failed structural inputs still need a stable quarantine path, but this
        # fallback itself is a FAIL health event and can never update latest.
        crawler_timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
        crawler_timestamp_basis = 'build clock fallback; source timestamp unavailable'
    batch_date = run_time[:10] if len(run_time)>=10 and run_time[4]=='-' else datetime.fromisoformat(crawler_timestamp).astimezone(ZoneInfo(settings['summary_run_time_timezone'])).date().isoformat()
    datetime.strptime(batch_date,'%Y-%m-%d')
    date_tag = batch_date.replace('-','')
    base = f'validation_packets/{batch_date}/Validation_Batch_{date_tag}'
    info = dict(batch_date=batch_date, crawler_filename=excel_path.name, crawler_timestamp=crawler_timestamp,
        crawler_timestamp_basis=crawler_timestamp_basis,
        summary_run_time=run_time, source_version=summary.get('crawler_version'), match_count=0,
        source_content_hash=cell_hash, source_file_sha256=hashlib.sha256(excel_path.read_bytes()).hexdigest(),
        data_path=base+'_DATA.json', qc_path=base+'_QC.md',
        excluded_catalog_counts={k:len(tables.get(k,[])) for k in ('Matches_To_Choose','Matches_Rejected')},
        table_inventory=inventory, redactions=redactions,
        configuration_hash=content_hash([settings,mapping,aliases,fingerprint]),
        policies=dict(history_timezone_offset_hours=settings['history_timezone_offset_hours'],
            alignment_max_gap_minutes=settings['alignment_max_gap_minutes'], alignment_min_companies=settings['alignment_min_companies'],
            bookmaker_registry_basis='inherited supplied V23 registry; namespace scoped; no name guessing',
            vip_odds_format=settings['vip_odds_format'], vip_odds_format_basis=settings['vip_odds_format_basis']))
    schema = detect_schema(tables,inventory,fingerprint,mapping)
    initial_events = list(schema['events'])
    if crawler_timestamp_basis.startswith('build clock'):
        initial_events.append(HealthEvent('SOURCE_TIMESTAMP_UNAVAILABLE','FAIL','No source timestamp could be parsed'))
    preliminary = RuleEngine(settings['health']['warning_count_pass_max']).evaluate(initial_events)
    if preliminary['status']=='FAIL':
        info['match_count']=len(tables.get('Matches_Selected',[]))
        health=dict(preliminary,schema_drift=schema['schema_drift'],schema=schema | {'events':[e.as_dict() for e in schema['events']]},
                    metrics={},historical_comparison={'baseline_available':False},matches={})
        data=dict(schema_version='1.0',batch_status='FAIL',batch_info=info,match_index=[],matches={},
                  batch_qc={'status':'FAIL','minimum_qc_passed':False,'duplicate_match_ids':[],
                            'unselected_market_match_ids':[],'match_index_qc':{}},health=health)
        return data, report(data), settings
    selected = tables.get('Matches_Selected',[])
    counts = Counter(identifier(r.get('match_id')) for r in selected)
    duplicate_ids = [k for k,v in counts.items() if v>1]
    if None in counts:
        raise ValueError('Missing selected match_id')
    mids = set(counts)
    unselected = sorted({identifier(r.get('match_id')) for name in TABLES for r in tables.get(name,[]) if identifier(r.get('match_id')) not in mids}, key=str)
    matches = {}
    for row in selected:
        mid = identifier(row['match_id'])
        if mid in matches:
            continue
        ko = timestamp(row.get('data_time'), crawler_timestamp, settings['kickoff_timezone_offset_hours'])
        ko_local = datetime.fromisoformat(ko).astimezone(timezone(timedelta(hours=settings['kickoff_timezone_offset_hours']))).isoformat() if ko else None
        status = 'finished' if row.get('is_finished') in (1,'1',True) else 'pre_match' if str(row.get('match_state'))=='0' else 'UNKNOWN'
        identity = dict(match_id=mid, league=row.get('league'), home_team=row.get('home_team'), away_team=row.get('away_team'),
            kickoff_time=ko_local, kickoff_utc=ko, kickoff_source='Titan JS zero-based month, Asia/Shanghai' if ko else 'UNKNOWN',
            crawler_filename=excel_path.name, crawler_timestamp=crawler_timestamp, source_version=info['source_version'], status=status)
        if not all(identity[k] for k in ('league','home_team','away_team')):
            raise ValueError(f'Incomplete match identity: {mid}')
        raw, timelines, records, duplicates = build_markets(tables, identity, mapping, settings, crawler_timestamp)
        slices = synchronize(timelines['1x2'], settings)
        q = quality(records, timelines, slices, duplicates, settings)
        source_tables = {name:[r for r in rows if identifier(r.get('match_id',r.get('Match_ID')))==mid]
                         for name,rows in tables.items() if name not in ('Matches_To_Choose','Matches_Rejected')}
        source_tables = {k:v for k,v in source_tables.items() if v}
        q['source_audit_issues'] = [dict(source_row=r['_source']['source_row'], market=r.get('Market'), company_id=r.get('Company_ID'),
                exact_duplicates=r.get('Exact_Duplicate_Count'), timestamp_collisions=r.get('Timestamp_Collision_Count'),
                parse_fail_count=r.get('Parse_Fail_Count'), aggregate_rows=r.get('Aggregate_Row_Count'), qc_status=r.get('QC_Status'))
            for r in source_tables.get('Data_Quality_Audit',[]) if any(r.get(k) not in (None,0,'0','') for k in ('Exact_Duplicate_Count','Timestamp_Collision_Count','Parse_Fail_Count','Aggregate_Row_Count'))]
        # Preserve every raw ladder row and source parser QC; unowned rows stay audit-only.
        q['raw_ladder_audit'] = dict(rows=len(source_tables.get('OverUnder_Ladder_Raw',[])),
            unverified_owner_rows=sum(not r.get('company_id') for r in source_tables.get('OverUnder_Ladder_Raw',[])),
            clean_rows=len(source_tables.get('OverUnder_Ladder_Clean',[])))
        if q['raw_ladder_audit']['unverified_owner_rows']:
            q['warnings'].append('raw_ladder_unverified_owner_rows_audit_only')
            if q['overall_status']=='PASS': q['overall_status']='WARN'
        lineup = source_tables.get('Lineup',[])
        context = dict(lineup=dict(status='source_reported' if lineup else 'missing',records=lineup),
            formation=[{k:r.get(k) for k in ('Home_Formation','Away_Formation')} for r in lineup],
            injuries=dict(status='unverified_candidates',records=source_tables.get('Lineup_Candidate',[])),
            suspensions=dict(status='unverified',records=[]),
            schedule=dict(home_recent=source_tables.get('Home_Recent',[]),away_recent=source_tables.get('Away_Recent',[])),
            future_schedule=dict(status='unstructured_source_context',records=source_tables.get('Analysis_Context',[])),
            team_strength=dict(status='raw_statistics_only',tech_stats=source_tables.get('Tech_Stats',[]),goal_distribution=source_tables.get('Goal_Distribution',[])),
            league_baseline=dict(status='missing'))
        matches[mid] = dict(match_identity=identity,data_quality=q,raw_market=raw,timeline=timelines,
            synchronized_slices=slices,context=context,calculations=calculate(raw,timelines,slices,settings),source_tables=source_tables)
    info['match_count'] = len(matches)
    index = build_index(matches,info,aliases)
    semantic=semantic_health(matches,settings)
    metrics=compute_metrics(matches,settings)
    history=load_valid_history(root,cell_hash,settings['health']['baseline_window'])
    comparison,history_events=compare_history(metrics,history,settings,list(matches))
    events=initial_events+semantic['events']+history_events
    if duplicate_ids:
        events.append(HealthEvent('DUPLICATE_MATCH_ID','FAIL','Matches_Selected contains duplicate match_id',tuple(duplicate_ids)))
    if unselected:
        events.append(HealthEvent('CROSS_MATCH_CONTAMINATION','FAIL','Market tables contain unselected match_id',tuple(str(x) for x in unselected)))
    for mid,packet in matches.items():
        q=packet['data_quality']
        packet_health=semantic['matches'][mid]
        q['timeline_status']=packet_health['timeline_status']
        q['synchronized_slice_health']=packet_health['synchronized_slice_status']
        q['ou_ladder_health']=packet_health['ou_ladder_status']
        packet['health']=packet_health
        if q['failures']:
            events.append(HealthEvent('MATCH_MINIMUM_QC_FAILURE','FAIL','Existing match integrity checks failed',(mid,),{'failures':q['failures']}))
        missing_1x2=[name for name,state in q['core_1x2'].items() if state=='missing']
        if missing_1x2:
            events.append(HealthEvent('CORE_1X2_PARTIAL_MISSING','WARN','A match is missing core 1X2 bookmakers',(mid,),{'companies':missing_1x2}))
        if q['record_issues'].get('unverified_bookmaker'):
            events.append(HealthEvent('NEW_OR_UNVERIFIED_BOOKMAKER','WARN','Unverified bookmaker rows are retained but excluded',(mid,),{'record_count':len(q['record_issues']['unverified_bookmaker'])}))
        if q['ladbrokes_ah']['status']=='unavailable':
            events.append(HealthEvent('LADBROKES_AH_KNOWN_EXCEPTION','INFO','Ladbrokes AH unavailable by known source exception',(mid,)))
    evaluated=RuleEngine(settings['health']['warning_count_pass_max']).evaluate(events)
    health=dict(evaluated,schema_drift=schema['schema_drift'],
        schema=schema | {'events':[e.as_dict() for e in schema['events']]},metrics=metrics,
        coverage_current=metrics['coverage'],coverage_previous_valid_batch=(comparison.get('baseline') or {}).get('coverage'),
        coverage_delta={m:{c:v.get('coverage_delta') for c,v in cs.items()} for m,cs in comparison.get('coverage',{}).items()},
        historical_comparison=comparison,matches=semantic['matches'])
    batch_qc = dict(status=health['status'],minimum_qc_passed=health['status']!='FAIL',
        duplicate_match_ids=duplicate_ids,unselected_market_match_ids=unselected,match_index_qc=index_qc(index))
    data = dict(schema_version='1.0',batch_status=health['status'],batch_info=info,match_index=index,matches=matches,batch_qc=batch_qc,health=health)
    if health['status']!='FAIL':
        validate_packet(data)
    return data, report(data), settings


def run(excel_path, root, dry_run=False):
    root = Path(root)
    try:
        data, qc_text, settings = build(excel_path,root)
    except Exception as exc:
        now=datetime.now(timezone.utc)
        try:
            source_hash=hashlib.sha256(Path(excel_path).read_bytes()).hexdigest()
        except OSError:
            source_hash='unavailable'
        batch_date=now.astimezone(ZoneInfo('America/Tijuana')).date().isoformat()
        tag=batch_date.replace('-','')
        info=dict(batch_date=batch_date,crawler_filename=Path(excel_path).name,
            crawler_timestamp=now.isoformat(timespec='seconds'),crawler_timestamp_basis='build clock after generation failure',
            summary_run_time=None,source_version='UNKNOWN',match_count=0,source_content_hash=source_hash,
            source_file_sha256=source_hash,data_path=f'validation_packets/{batch_date}/Validation_Batch_{tag}_DATA.json',
            qc_path=f'validation_packets/{batch_date}/Validation_Batch_{tag}_QC.md',excluded_catalog_counts={},
            table_inventory=[],redactions=[],configuration_hash='UNKNOWN',policies={})
        evaluated=RuleEngine().evaluate([HealthEvent('DATA_GENERATION_FAILED','FAIL',str(exc))])
        health=dict(evaluated,schema_drift=True,schema={},metrics={},historical_comparison={},matches={})
        data=dict(schema_version='1.0',batch_status='FAIL',batch_info=info,match_index=[],matches={},
            batch_qc={'status':'FAIL','minimum_qc_passed':False,'duplicate_match_ids':[],
                      'unselected_market_match_ids':[],'match_index_qc':{}},health=health)
        qc_text=report(data)
        data_path,qc_path=publish_failed(root,data,qc_text)
        return dict(status='QC_FAILED',batch_status='FAIL',match_count=0,warning_count=0,
            critical_error_count=1,latest_updated=False,data_path=data_path,qc_path=qc_path,
            error='DATA_GENERATION_FAILED: '+str(exc))
    if data['batch_status']=='FAIL':
        data_path,qc_path=publish_failed(root,data,qc_text)
        return dict(status='QC_FAILED',batch_status='FAIL',match_count=data['batch_info']['match_count'],
            warning_count=data['health']['warning_count'],critical_error_count=data['health']['critical_error_count'],
            latest_updated=False,data_path=data_path,qc_path=qc_path,
            error='Fail-closed health gate blocked latest and Git publication')
    is_unchanged = unchanged(root,data)
    existing = root / data['batch_info']['data_path']
    if existing.exists() and not is_unchanged:
        old = json.loads(existing.read_text(encoding='utf-8'))
        if old['batch_info']['crawler_timestamp'] > data['batch_info']['crawler_timestamp']:
            return dict(status='STALE_SOURCE',match_count=data['batch_info']['match_count'],error='Refusing to replace newer same-day batch with older source')
    if not is_unchanged or not (root/'validation_packets/latest.json').exists() or not (root/data['batch_info']['qc_path']).exists():
        publish_files(root,data,qc_text)
    result = dict(status='NO_CHANGES' if is_unchanged else 'DRY_RUN' if dry_run else 'GENERATED',
        batch_status=data['batch_status'],match_count=data['batch_info']['match_count'],
        warning_count=data['health']['warning_count'],critical_error_count=data['health']['critical_error_count'],
        latest_updated=True,data_path=data['batch_info']['data_path'],qc_path=data['batch_info']['qc_path'],latest_path='validation_packets/latest.json')
    if not dry_run:
        from src.export.git_publish import publish_git
        result.update(publish_git(root,data['batch_info'],settings))
    return result
