import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .match_index_builder import normalize, league_name


class MatchResolver:
    def __init__(self, index, registry=None):
        self.index = index
        self.registry = registry or {'leagues': {}}

    def resolve_match(self, query, league=None, date=None, kickoff=None):
        q = normalize(query)
        q = re.sub(r'^(请)?分析\s*', '', q)
        q = re.sub(r'(这场|那场|比赛)$', '', q).strip()
        today = datetime.now(timezone(timedelta(hours=8))).date()
        for token, delta in [('今天', 0), ('今晚', 0), ('明天', 1), ('昨天', -1)]:
            if token in q:
                date = date or (today + timedelta(days=delta)).isoformat()
                q = q.replace(token, '').strip()
        found_date = re.search(r'\d{4}-\d{2}-\d{2}', q)
        if found_date:
            date = date or found_date[0]
            q = q.replace(found_date[0], '').strip()
        for canonical, names in self.registry['leagues'].items():
            for name in sorted(names, key=len, reverse=True):
                if normalize(name) in q:
                    league = league or canonical
                    q = q.replace(normalize(name), '').strip()
        q = q.strip(' 的')
        rows = list(self.index)
        if league:
            norm_league = normalize(league_name(league, self.registry))
            rows = [r for r in rows if norm_league in (normalize(r['league']), normalize(r['league_normalized']))]
        if date:
            rows = [r for r in rows if r['kickoff_date'] == str(date)]
        if kickoff:
            rows = [r for r in rows if str(kickoff) in str(r['kickoff_time'])]
        pair = re.split(r'\s*(?:\bvs\.?\b|对阵|对|—)\s*', q)
        def full(r):
            return q == normalize(f"{r['home_team']} vs {r['away_team']}")
        def teams(r):
            return len(pair) == 2 and pair[0] in map(normalize, r['home_aliases']) and pair[1] in map(normalize, r['away_aliases'])
        def single(r):
            return q in map(normalize, r['home_aliases'] + r['away_aliases'])
        methods = [('full_fixture', full), ('home_team+away_team', teams),
                   ('fixture_aliases', lambda r: q in map(normalize, r['fixture_aliases'])),
                   ('team+league' if league else 'team+date' if date else 'team+kickoff' if kickoff else 'team', single)]
        matched, by = [], None
        for method, predicate in methods:
            matched = [r for r in rows if predicate(r)]
            if matched:
                by = method
                break
        candidates = [dict(match_id=r['match_id'], league=r['league'], fixture=f"{r['home_team']} vs {r['away_team']}", kickoff=r['kickoff_time']) for r in matched]
        result = dict(status='resolved' if len(matched) == 1 else 'ambiguous' if matched else 'not_found',
                      match_id=matched[0]['match_id'] if len(matched) == 1 else None,
                      confidence='exact' if len(matched) == 1 else None, matched_by=by,
                      candidate_count=len(matched), candidates=candidates)
        if len(matched) == 1:
            result['resolved_from'] = matched[0].get('resolved_from')
        return result


def load_index(root):
    """Newest containing batch wins; duplicate IDs retain source-selection audit."""
    selected, alternatives = {}, {}
    for path in sorted((Path(root) / 'validation_packets').glob('**/*_DATA.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        info = data['batch_info']
        for row in data['match_index']:
            mid = row['match_id']
            completeness = data['matches'][mid]['data_quality'].get('valid_quote_count', 0)
            version = tuple(int(x) for x in re.findall(r'\d+', str(info['source_version'])))
            rank = (info['batch_date'], info.get('crawler_timestamp') or '', completeness, version)
            alternatives.setdefault(mid, []).append(dict(batch_file=path.relative_to(root).as_posix(),
                crawler_timestamp=info.get('crawler_timestamp'), completeness=completeness, source_version=info.get('source_version')))
            if mid not in selected or rank > selected[mid][0]:
                copy = dict(row)
                copy['resolved_from'] = dict(row['resolved_from'], batch_file=path.relative_to(root).as_posix())
                selected[mid] = (rank, copy)
    for mid, (_, row) in selected.items():
        row['resolved_from']['source_candidates'] = [dict(x, selected=x['batch_file'] == row['resolved_from']['batch_file']) for x in alternatives[mid]]
    return [value[1] for value in selected.values()]


def resolve_match(query, league=None, date=None, kickoff=None):
    root = Path(__file__).resolve().parents[2]
    registry = json.loads((root / 'config/team_aliases.json').read_text(encoding='utf-8'))
    return MatchResolver(load_index(root), registry).resolve_match(query, league, date, kickoff)
