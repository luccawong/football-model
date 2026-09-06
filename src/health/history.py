import json
from pathlib import Path
from src.export.files import atomic_write, encoded


def history_path(root):
    return Path(root)/'validation_packets/history_index.json'


def update_history(root, data):
    path=history_path(root)
    value={'schema_version':'1.0','batches':[]}
    if path.exists():
        value=json.loads(path.read_text(encoding='utf-8'))
    info=data['batch_info']
    entry={'batch_date':info['batch_date'],'crawler_timestamp':info['crawler_timestamp'],
        'source_file':info['crawler_filename'],'source_content_hash':info['source_content_hash'],
        'health_status':data['health']['status'],'data_path':info['data_path'],'qc_path':info['qc_path'],
        'commit_sha':None,'match_count':info['match_count']}
    existing=next((e for e in value['batches'] if e.get('source_content_hash')==info['source_content_hash']),None)
    if existing:
        commit=existing.get('commit_sha')
        existing.update(entry)
        existing['commit_sha']=commit
    else:
        value['batches'].append(entry)
    value['batches'].sort(key=lambda e:(e['batch_date'],e.get('crawler_timestamp') or '',e['source_content_hash']))
    atomic_write(path,encoded(value))


def record_commit(root, source_hash, commit_sha):
    path=history_path(root)
    if not path.exists():
        return False
    value=json.loads(path.read_text(encoding='utf-8'))
    changed=False
    for entry in value.get('batches',[]):
        if entry.get('source_content_hash')==source_hash and entry.get('commit_sha')!=commit_sha:
            entry['commit_sha']=commit_sha
            changed=True
    if changed:
        atomic_write(path,encoded(value))
    return changed
