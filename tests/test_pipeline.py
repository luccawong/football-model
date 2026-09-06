import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from openpyxl import Workbook
from src.bookmaker.identity import identify
from src.calculations.odds import devig, movements
from src.index.match_index_builder import build_index
from src.index.match_resolver import MatchResolver
from src.normalization.formats import timestamp, line_value, decimal_prices
from src.normalization.markets import normalize_row, ownership_issues
from src.timeline.slices import deduplicate, synchronize
from src.qc.checks import quality, validate_packet
from src.export.files import publish_files, unchanged
from src.export.security import sanitize, scan_text
from src.export.git_publish import publish_git
from src.pipeline import build

ROOT=Path(__file__).resolve().parents[1]
SETTINGS=json.loads((ROOT/'config/settings.json').read_text())
MAPPING=json.loads((ROOT/'config/bookmaker_mapping.json').read_text(encoding='utf-8'))
ALIASES=json.loads((ROOT/'config/team_aliases.json').read_text(encoding='utf-8'))
ANCHOR='2026-09-05T19:26:00+00:00'
MATCH=dict(match_id='123',league='葡超',home_team='葡萄牙体育',away_team='葡萄牙国民',status='pre_match')


def quote(cid='115',time='2026-09-06 03:00',row=2,mid='123',odds=(2,3,4)):
    r=dict(match_id=mid,league=MATCH['league'],home_team=MATCH['home_team'],away_team=MATCH['away_team'],
           company_id=cid,company_raw='William Hill' if cid=='115' else 'Ladbrokes',
           change_time=time,home_odds=odds[0],draw_odds=odds[1],away_odds=odds[2],
           _source=dict(source_sheet='test',source_table='Europe_1x2_History',source_row=row))
    return normalize_row(r,'Europe_1x2_History','history',MATCH,MAPPING,SETTINGS,ANCHOR)


def synthetic(path):
    w=Workbook()
    w.remove(w.active)
    data={
        'Summary':[{'metric':'run_time','value':'2026-09-05 12:26:00'},{'metric':'crawler_version','value':'23.2.8'}],
        'Matches_Selected':[dict(MATCH,match_time='03:30',data_time='2026,8,6,03,30,00',match_state='0')],
        'Europe_1x2':[], 'Europe_1x2_History':[], 'Asian_Current':[], 'Asian_History':[],
        'OverUnder_Current':[], 'OverUnder_History':[], 'OverUnder_Ladder_Clean':[]}
    one={'115':'William Hill','82':'Ladbrokes','104':'Interwetten','177':'Pinnacle','281':'Bet 365','80':'Macauslot'}
    for cid,name in one.items():
        data['Europe_1x2'].append(dict(MATCH,company_id=cid,company_raw=name,initial_home=2,initial_draw=3,initial_away=4,current_home=1.9,current_draw=3.1,current_away=4.1))
        data['Europe_1x2_History'] += [dict(MATCH,company_id=cid,company_raw=name,home_odds=2,draw_odds=3,away_odds=4,change_time='2026-09-06 02:00',is_opening=1),dict(MATCH,company_id=cid,company_raw=name,home_odds=1.9,draw_odds=3.1,away_odds=4.1,change_time='2026-09-06 03:00',is_opening=0)]
    vip={'1':'澳*','47':'平*','8':'36*','48':'香港马*','3':'Crow*'}
    for cid,name in vip.items():
        data['Asian_Current'].append(dict(MATCH,company_id=cid,company_raw=name,initial_left=.9,initial_line='半球',initial_right=.9,current_left=.9,current_line='半球',current_right=.9))
        data['Asian_History'] += [dict(MATCH,company_id=cid,company_raw=name,left_water=.9,market_line='半球',right_water=.9,change_time='9-6 02:00',Record_Type='HISTORY_EVENT'),dict(MATCH,company_id=cid,company_raw=name,left_water=.91,market_line='半球',right_water=.89,change_time='9-6 03:00',Record_Type='HISTORY_EVENT')]
    for cid,name in {'1':'澳*','47':'平*','8':'36*'}.items():
        data['OverUnder_Current'].append(dict(MATCH,company_id=cid,company_raw=name,initial_left=.9,initial_line='2.5',initial_right=.9,current_left=.9,current_line='2.5',current_right=.9))
        data['OverUnder_History'] += [dict(MATCH,company_id=cid,company_raw=name,left_water=.9,market_line='2.5',right_water=.9,change_time='9-6 02:00',Record_Type='HISTORY_EVENT'),dict(MATCH,company_id=cid,company_raw=name,left_water=.91,market_line='2.5',right_water=.89,change_time='9-6 03:00',Record_Type='HISTORY_EVENT')]
        data['OverUnder_Ladder_Clean'] += [dict(MATCH,company_id=cid,company_raw=name,line_type=kind,
            opening_line_raw=line,current_line_raw=line,opening_over_raw=.9,opening_under_raw=.9,
            current_over_raw=.9,current_under_raw=.9,opening_odds_format='HK',current_odds_format='HK',
            observed_at_utc=ANCHOR) for kind,line in [('MAIN','2.5'),('ALTERNATIVE','2.75')]]
    for name,rows in data.items():
        s=w.create_sheet(name)
        headers=list(rows[0])
        s.append(headers)
        for row in rows:s.append([row.get(k) for k in headers])
    w.save(path)


class PipelineTests(unittest.TestCase):
    def test_match_id_no_contamination(self):
        r=quote(mid='999')
        self.assertIn('cross_match_id',r['issues'])
        self.assertIsNone(r['devig'])

    def test_company_mapping(self):
        self.assertEqual(identify({'company_id':'115'},'1x2',MAPPING)['company_normalized_name'],'William Hill')

    def test_namespaces(self):
        self.assertEqual(identify({'company_id':'8'},'ah',MAPPING)['company_normalized_name'],'Bet365')
        self.assertIsNone(identify({'company_id':'8'},'1x2',MAPPING)['company_normalized_name'])

    def test_planetwin_not_bet365(self):
        self.assertEqual(identify({'company_id':'986','company_raw':'PlanetWin365'},'1x2',MAPPING)['company_normalized_name'],'PlanetWin365')

    def test_masked_name_not_ladbrokes(self):
        self.assertEqual(identify({'company_id':'31','company_raw':'利*'},'ah',MAPPING)['identity_status'],'unverified')

    def test_ladbrokes_regions_not_merged(self):
        self.assertNotEqual(identify({'company_id':'82'},'1x2',MAPPING)['company_normalized_name'],identify({'company_id':'1135'},'1x2',MAPPING)['company_normalized_name'])

    def test_raw_name_conflict(self):
        self.assertEqual(identify({'company_id':'281','company_raw':'PlanetWin365'},'1x2',MAPPING)['identity_status'],'conflict')

    def test_ladbrokes_ah_allowed(self):
        q=quality([quote()],{'1x2':{},'ah':{},'ou':{}},[],[],SETTINGS)
        self.assertTrue(q['minimum_qc_passed'])
        self.assertEqual(q['ladbrokes_ah']['confidence_penalty'],'none_by_default')

    def test_ladbrokes_1x2_missing_warning(self):
        q=quality([quote()],{'1x2':{},'ah':{},'ou':{}},[],[],SETTINGS)
        self.assertIn('missing_1x2:Ladbrokes UK',q['warnings'])

    def test_timeline_sorted(self):
        rows,_=deduplicate([quote(time='2026-09-06 03:05'),quote(time='2026-09-06 03:00',row=3)])
        self.assertLess(rows[0]['timestamp'],rows[1]['timestamp'])

    def test_duplicate_detection(self):
        rows,duplicates=deduplicate([quote(),quote(row=3)])
        self.assertEqual((len(rows),len(duplicates)),(1,1))

    def test_different_matches_not_deduped(self):
        r=quote(); other=copy.deepcopy(r);other['match_id']='456'
        self.assertEqual(len(deduplicate([r,other])[0]),2)

    def test_different_lines_not_deduped(self):
        r=quote(); other=copy.deepcopy(r);other['line']=2.5
        self.assertEqual(len(deduplicate([r,other])[0]),2)

    def test_synchronized_gap(self):
        a,b=quote(),quote(cid='82',time='2026-09-06 01:00',row=3)
        slices=synchronize({'europe_1x2:115':[a],'europe_1x2:82':[b]},SETTINGS)
        self.assertEqual(slices[-1]['companies']['europe_1x2:82']['time_gap_minutes'],120)
        self.assertEqual(slices[-1]['alignment_status'],'weak_alignment')
        self.assertEqual(slices[-1]['probability_differences'],[])

    def test_synchronized_match_scope(self):
        a=quote()
        self.assertEqual(synchronize({'europe_1x2:115':[a]},SETTINGS)[0]['alignment_status'],'weak_alignment')

    def test_devig_sum(self):
        probs=devig([1.91,3.5,4.5],['home','draw','away'])['probabilities']
        self.assertAlmostEqual(sum(probs.values()),1)
        self.assertAlmostEqual(probs['home'],(1/1.91)/(1/1.91+1/3.5+1/4.5))

    def test_hk_conversion(self):
        self.assertEqual(decimal_prices([.8,1.02],'HK')[0],[1.8,2.02])

    def test_impossible_odds(self):
        self.assertIsNone(decimal_prices([0,-1],'DECIMAL')[0])

    def test_ah_line_sign_and_split(self):
        self.assertEqual(line_value('两球/两球半','ah'),-2.25)
        self.assertEqual(line_value('受半球','ah'),.5)

    def test_ah_moves_separate(self):
        a=dict(line=-.75,prices=[.8,1],record_id='a')
        b=dict(line=-1,prices=[.9,.9],record_id='b')
        c=dict(line=-1,prices=[1,.8],record_id='c')
        self.assertEqual([r['kind'] for r in movements([a,b,c])],['line_move','price_move'])

    def test_titan_zero_month(self):
        self.assertEqual(timestamp('2026,8,6,03,30,00',ANCHOR,8),'2026-09-05T19:30:00+00:00')

    def test_unknown_timezone_not_guessed(self):
        self.assertIsNone(timestamp('2026,09-1,05,19,05,00',ANCHOR,None))

    def test_year_rollover(self):
        self.assertEqual(timestamp('12-31 20:00','2027-01-01T00:00:00+00:00',8),'2026-12-31T12:00:00+00:00')

    def test_odds_history_sid(self):
        row=dict(MATCH,company_id='115',data_id='777',source_url='https://op1.titan007.com/OddsHistory.aspx?id=777&sid=123&cid=115')
        self.assertEqual(ownership_issues(row,MATCH,'1x2'),[])
        row['source_url']=row['source_url'].replace('sid=123','sid=999')
        self.assertIn('cross_match_url',ownership_issues(row,MATCH,'1x2'))

    def test_alias_examples(self):
        fixtures=[('2993781','国际米兰','那不勒斯'),('3003876','曼彻斯特城','考文垂'),('3013673','毕尔巴鄂竞技','马德里竞技')]
        packets={mid:dict(match_identity=dict(match_id=mid,home_team=h,away_team=a,league='test',kickoff_time='2026-09-06T03:00:00+08:00',status='pre_match')) for mid,h,a in fixtures}
        info=dict(crawler_filename='test.xlsx',batch_date='2026-09-05',data_path='test_DATA.json',crawler_timestamp=ANCHOR,source_version='23')
        resolver=MatchResolver(build_index(packets,info,ALIASES),ALIASES)
        for q,mid in [('国米','2993781'),('国米 vs 那不勒斯','2993781'),('曼城','3003876'),('毕尔巴鄂 vs 马竞','3013673')]:
            with self.subTest(query=q): self.assertEqual(resolver.resolve_match(q)['match_id'],mid)

    def test_ambiguous_no_guess(self):
        packets={str(i):dict(match_identity=dict(home_team='拜仁慕尼黑',away_team=a,league=l,kickoff_time='2026-09-06T03:00:00+08:00',status='pre_match')) for i,a,l in [(1,'多特蒙德','德甲'),(2,'巴黎圣日耳曼','欧冠')]}
        info=dict(crawler_filename='x.xlsx',batch_date='2026-09-05',data_path='x',crawler_timestamp=ANCHOR,source_version='23')
        resolver=MatchResolver(build_index(packets,info,ALIASES),ALIASES)
        self.assertEqual(resolver.resolve_match('分析拜仁')['status'],'ambiguous')
        self.assertEqual(resolver.resolve_match('分析拜仁',league='Bundesliga')['match_id'],'1')

    def test_security_redaction(self):
        audit=[]
        result=sanitize({'password':'dummy-pass','source':str(Path('C:/Users/example/private/input.xlsx'))},audit)
        self.assertEqual(result['password'],'[REDACTED]')
        self.assertNotIn('example',result['source'])

    def test_https_url_not_redacted_as_drive_path(self):
        audit=[]
        url='https://vip.titan007.com/AsianOdds_n.aspx?id=123'
        self.assertEqual(sanitize(url,audit),url)
        self.assertEqual(audit,[])

    def test_synthetic_batch_ladder_and_latest(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'arbitrary_filename.xlsx';synthetic(path)
            data,text,_=build(path,ROOT)
            self.assertEqual(data['batch_info']['match_count'],1)
            self.assertEqual(len(data['matches']['123']['calculations']['ou_ladder']),12)
            self.assertEqual(len(data['matches']['123']['source_tables']['OverUnder_Ladder_Clean']),6)
            publish_files(Path(d),data,text)
            latest=json.loads((Path(d)/'validation_packets/latest.json').read_text(encoding='utf-8'))
            self.assertTrue((Path(d)/latest['data_path']).is_file())
            self.assertTrue((Path(d)/latest['qc_path']).is_file())
            self.assertTrue(unchanged(Path(d),data))
            self.assertNotIn('codex_path',latest)
            validate_packet(data)

    def test_no_change_no_commit(self):
        calls=[]
        def fake(root,*args,**kwargs):
            calls.append(args)
            out=''
            if args[0]=='branch':out='main'
            if args[:2]==('remote','get-url'):out=SETTINGS['git_url']
            if args[0]=='rev-parse':out='abc'
            if args[0]=='ls-remote':out='abc refs/heads/main'
            return type('Result',(),{'stdout':out,'returncode':0})()
        with tempfile.TemporaryDirectory() as d, patch('src.export.git_publish.git',side_effect=fake):
            result=publish_git(Path(d),dict(batch_date='2026-09-05',match_count=2,source_content_hash='test'),SETTINGS)
        self.assertFalse(any(c[0]=='commit' for c in calls))
        self.assertEqual(result['changes'],'NO_CHANGES')

    def test_push_failure_honest(self):
        with tempfile.TemporaryDirectory() as d, patch('src.export.git_publish.git',side_effect=RuntimeError('authentication failed')):
            result=publish_git(Path(d),dict(batch_date='2026-09-05',match_count=2),SETTINGS)
        self.assertEqual(result['status'],'PUSH_FAILED')
        self.assertIn('authentication',result['error'])


if __name__=='__main__':unittest.main()
