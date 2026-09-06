import itertools
import re
import unicodedata


def normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', str(text or '')).casefold()).strip()


def aliases(name, registry):
    groups = [g for g in registry['teams'] if normalize(name) in {normalize(v) for v in g}]
    return sorted(set([name] + (groups[0] if len(groups) == 1 else []))), len(groups) == 1


def league_name(name, registry):
    return next((k for k, values in registry['leagues'].items() if normalize(name) in map(normalize, values)), name)


def build_index(matches, info, registry):
    result = []
    for mid, packet in matches.items():
        m = packet['match_identity']
        home, hm = aliases(m['home_team'], registry)
        away, am = aliases(m['away_team'], registry)
        league = league_name(m['league'], registry)
        kickoff = m.get('kickoff_time')
        result.append(dict(match_id=mid, league=m['league'], league_normalized=league,
            home_team=m['home_team'], away_team=m['away_team'], home_aliases=home, away_aliases=away,
            fixture_aliases=[f'{h} vs {a}' for h, a in itertools.product(home, away)],
            kickoff_time=kickoff, kickoff_date=kickoff[:10] if kickoff else None,
            competition_type=registry['competition_types'].get(league),
            source_file=info['crawler_filename'], crawler_batch=info['batch_date'],
            status=m['status'], unresolved_team_mapping=[role for role, ok in [('home', hm), ('away', am)] if not ok],
            date_basis='kickoff local Asia/Shanghai',
            resolved_from=dict(batch_file=info['data_path'], crawler_file=info['crawler_filename'],
                               crawler_timestamp=info['crawler_timestamp'], source_version=info['source_version'])))
    return result
