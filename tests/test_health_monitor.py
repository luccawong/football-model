import copy
import json
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook
from src.health.schema import detect_schema
from src.health.metrics import compare_history
from src.health.rules import HealthEvent, RuleEngine
from src.health.semantic import semantic_health
from src.export.files import publish_files
from src.pipeline import run

ROOT=Path(__file__).resolve().parents[1]
SETTINGS=json.loads((ROOT/'config/settings.json').read_text(encoding='utf-8'))
MAPPING=json.loads((ROOT/'config/bookmaker_mapping.json').read_text(encoding='utf-8'))
FINGERPRINT=json.loads((ROOT/'config/schema_fingerprint.json').read_text(encoding='utf-8'))


def schema_fixture():
    tables={}
    inventory=[]
    for name,spec in FINGERPRINT['tables'].items():
        row={column:'1' for column in spec['required_columns']}
        if name=='Matches_Selected':
            row.update(match_id='1',league='L',match_time='12:00',data_time='2026,8,5,12,00,00',match_state='0',home_team='H',away_team='A')
        tables[name]=[row]
        inventory.append({'table':name,'sheet':'All_In_One','rows':1,'declared_rows':1,
            'columns':spec['required_columns']+spec.get('optional_columns',[]),'observed_dtypes':{}})
    return tables,inventory


def base_metrics(ladbrokes=1,ladder=8):
    return {'coverage':{'1x2':{'Ladbrokes UK':ladbrokes,'Bet365':1},'ah':{},'ou':{}},
        'average_bookmakers_per_match':10,'average_ou_ladder_unique_lines_per_core_company':ladder,
        'average_timeline_rows_per_match':{'1x2':100,'ah':50,'ou':40},
        'unverified_bookmaker_record_rate':0,'duplicate_row_rate':0,'missing_timestamp_rate':0}


def minimal_failed_workbook(path):
    w=Workbook();s=w.active;s.title='Summary';s.append(['metric','value']);s.append(['run_time','2026-09-05 12:00:00']);s.append(['crawler_version','broken'])
    w.save(path)


class HealthMonitorTests(unittest.TestCase):
    def test_critical_sheet_missing_fails(self):
        tables,inventory=schema_fixture();del tables['Europe_1x2_History'];inventory=[i for i in inventory if i['table']!='Europe_1x2_History']
        result=detect_schema(tables,inventory,FINGERPRINT,MAPPING)
        health=RuleEngine().evaluate(result['events'])
        self.assertEqual(health['status'],'FAIL')
        self.assertIn('CRITICAL_SHEET_MISSING',health['reason_codes'])

    def test_unrelated_column_is_info(self):
        tables,inventory=schema_fixture();inventory[0]['columns'].append('new_harmless_column')
        result=detect_schema(tables,inventory,FINGERPRINT,MAPPING)
        self.assertNotEqual(RuleEngine().evaluate(result['events'])['status'],'FAIL')
        self.assertIn('UNKNOWN_COLUMNS_ADDED',[e.code for e in result['events']])

    def test_required_column_rename_fails(self):
        tables,inventory=schema_fixture();item=next(i for i in inventory if i['table']=='Matches_Selected')
        item['columns'].remove('match_id');item['columns'].append('Match_ID')
        events=detect_schema(tables,inventory,FINGERPRINT,MAPPING)['events']
        self.assertIn('REQUIRED_COLUMN_RENAMED',[e.code for e in events])
        self.assertEqual(RuleEngine().evaluate(events)['status'],'FAIL')

    def test_bet365_pollution_fails(self):
        tables,inventory=schema_fixture();mapping=copy.deepcopy(MAPPING)
        mapping['europe_1x2:281']['normalized_name']='PlanetWin365'
        health=RuleEngine().evaluate(detect_schema(tables,inventory,FINGERPRINT,mapping)['events'])
        self.assertIn('BET365_IDENTITY_POLLUTION',health['reason_codes'])

    def test_masked_ladbrokes_mapping_fails(self):
        tables,inventory=schema_fixture();mapping=copy.deepcopy(MAPPING)
        mapping['vip:31']={'verified':True,'normalized_name':'Ladbrokes UK','raw_name':['利*']}
        health=RuleEngine().evaluate(detect_schema(tables,inventory,FINGERPRINT,mapping)['events'])
        self.assertIn('MASKED_NAME_MAPPED_TO_LADBROKES',health['reason_codes'])

    def test_ladbrokes_known_exception_is_info(self):
        result=RuleEngine().evaluate([HealthEvent('LADBROKES_AH_KNOWN_EXCEPTION','INFO','known')])
        self.assertEqual(result['status'],'PASS')

    def test_ladbrokes_single_match_missing_warns(self):
        result=RuleEngine().evaluate([HealthEvent('CORE_1X2_PARTIAL_MISSING','WARN','missing',('1',),{'companies':['Ladbrokes UK']})])
        self.assertEqual(result['status'],'WARN')

    def test_ladbrokes_batch_collapse_fails(self):
        current=base_metrics(ladbrokes=0)
        comparison,events=compare_history(current,[base_metrics(ladbrokes=1)],SETTINGS,['1','2'])
        health=RuleEngine().evaluate(events)
        self.assertEqual(health['status'],'FAIL')
        self.assertIn('LADBROKES_1X2_COVERAGE_COLLAPSE',health['reason_codes'])
        self.assertEqual(comparison['coverage']['1x2']['Ladbrokes UK']['coverage_delta'],-1)

    def test_cross_match_event_fails(self):
        self.assertEqual(RuleEngine().evaluate([HealthEvent('CROSS_MATCH_CONTAMINATION','FAIL','bad',('1',))])['status'],'FAIL')

    def test_impossible_odds_event(self):
        self.assertEqual(RuleEngine().evaluate([HealthEvent('IMPOSSIBLE_ODDS_OR_LINE','WARN','zero',('1',))])['status'],'WARN')

    def test_devig_error_fails(self):
        self.assertEqual(RuleEngine().evaluate([HealthEvent('DEVIG_SUM_INVALID','FAIL','bad')])['status'],'FAIL')

    def test_timeline_reverse_warns(self):
        self.assertEqual(RuleEngine().evaluate([HealthEvent('TIMELINE_SOURCE_REVERSE_ORDER','WARN','reverse')])['status'],'WARN')

    def test_ladder_collapse_alert(self):
        current=base_metrics(ladder=1)
        _,events=compare_history(current,[base_metrics(ladder=8)],SETTINGS,['1'])
        event=next(e for e in events if e.code=='OU_LADDER_DEGRADATION')
        self.assertEqual(event.severity,'FAIL')

    def test_identical_duplicate_is_info_safe(self):
        self.assertEqual(RuleEngine().evaluate([HealthEvent('IDENTICAL_DUPLICATE_DEDUPED','INFO','safe')])['status'],'PASS')

    def test_conflicting_duplicate_warns(self):
        self.assertEqual(RuleEngine().evaluate([HealthEvent('CONFLICTING_DUPLICATE','WARN','conflict')])['status'],'WARN')

    def test_fail_batch_does_not_create_latest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'config').mkdir()
            for name in ('settings.json','bookmaker_mapping.json','team_aliases.json','schema_fingerprint.json'):
                (root/'config'/name).write_bytes((ROOT/'config'/name).read_bytes())
            x=root/'broken.xlsx';minimal_failed_workbook(x)
            result=run(x,root,dry_run=True)
            self.assertEqual(result['batch_status'],'FAIL')
            self.assertFalse((root/'validation_packets/latest.json').exists())
            self.assertTrue((root/result['qc_path']).exists())

    def test_previous_latest_survives_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'config').mkdir()
            for name in ('settings.json','bookmaker_mapping.json','team_aliases.json','schema_fingerprint.json'):
                (root/'config'/name).write_bytes((ROOT/'config'/name).read_bytes())
            latest=root/'validation_packets/latest.json';latest.parent.mkdir();latest.write_text('{"sentinel":true}\n',encoding='utf-8')
            before=latest.read_bytes();x=root/'broken.xlsx';minimal_failed_workbook(x)
            run(x,root,dry_run=True)
            self.assertEqual(latest.read_bytes(),before)

    def test_pass_batch_updates_latest_with_health(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            data={'batch_info':{'batch_date':'2026-09-05','crawler_timestamp':'2026-09-05T00:00:00+00:00','crawler_filename':'x.xlsx','source_version':'1','source_content_hash':'abc','match_count':0,'data_path':'validation_packets/2026-09-05/x_DATA.json','qc_path':'validation_packets/2026-09-05/x_QC.md'},
                'match_index':[],'matches':{},'health':{'status':'PASS','warning_count':0,'critical_error_count':0,'schema_drift':False}}
            publish_files(root,data,'# QC\n')
            latest=json.loads((root/'validation_packets/latest.json').read_text(encoding='utf-8'))
            self.assertEqual(latest['health']['status'],'PASS')
            self.assertEqual(latest['health']['qc_path'],data['batch_info']['qc_path'])


if __name__=='__main__':unittest.main()
