import hashlib
import json
import os
from pathlib import Path


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def content_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    try:
        temp.write_bytes(content)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def unchanged(root, data):
    old_path = root / data['batch_info']['data_path']
    if not old_path.exists():
        return False
    old = json.loads(old_path.read_text(encoding='utf-8'))
    return old == data


def publish_files(root, data, report):
    info = data['batch_info']
    data_path, qc_path = root / info['data_path'], root / info['qc_path']
    if data_path.exists() and not unchanged(root, data):
        # Preserve prior same-day batch before replacing stable dated entry.
        previous = data_path.read_bytes()
        old = json.loads(previous.decode('utf-8'))
        # A code/schema improvement over the exact same crawler content is a
        # regenerated view, not a new source revision. Archive only distinct
        # crawler content so development runs cannot inflate the repository.
        if old.get('batch_info',{}).get('source_content_hash') != info.get('source_content_hash'):
            suffix = hashlib.sha256(previous).hexdigest()[:16]
            archive = data_path.parent / 'revisions' / suffix
            atomic_write(archive / data_path.name, previous)
            if qc_path.exists():
                atomic_write(archive / qc_path.name, qc_path.read_bytes())
    latest = dict(batch_date=info['batch_date'], crawler_timestamp=info['crawler_timestamp'],
        source_file=info['crawler_filename'], source_version=info['source_version'],
        data_path=info['data_path'], qc_path=info['qc_path'], match_count=info['match_count'],
        match_index=data['match_index'], source_content_hash=info['source_content_hash'],
        health={'status':data['health']['status'],'warning_count':data['health']['warning_count'],
                'critical_error_count':data['health']['critical_error_count'],
                'schema_drift':data['health']['schema_drift'],'qc_path':info['qc_path']})
    atomic_write(data_path, encoded(data))
    atomic_write(qc_path, report.encode('utf-8'))
    latest_path = root / 'validation_packets/latest.json'
    if latest_path.exists():
        old = json.loads(latest_path.read_text(encoding='utf-8'))
        if (old['batch_date'], old.get('crawler_timestamp') or '') > (latest['batch_date'], latest['crawler_timestamp'] or ''):
            return False
    atomic_write(latest_path, encoded(latest))
    from src.health.history import update_history
    update_history(root,data)
    return True


def publish_failed(root,data,report):
    info=data['batch_info']
    tag=info['batch_date'].replace('-','')
    directory=Path(root)/'failed_batches'/info['batch_date']
    data_path=directory/f'Validation_Batch_{tag}_FAILED_DATA.json'
    qc_path=directory/f'Validation_Batch_{tag}_FAILED_QC.md'
    # Never overwrite a different failed source without preserving both.
    if data_path.exists():
        old=json.loads(data_path.read_text(encoding='utf-8'))
        if old.get('batch_info',{}).get('source_content_hash')!=info.get('source_content_hash'):
            suffix=info.get('source_content_hash','unknown')[:16]
            data_path=directory/f'Validation_Batch_{tag}_{suffix}_FAILED_DATA.json'
            qc_path=directory/f'Validation_Batch_{tag}_{suffix}_FAILED_QC.md'
    data['batch_info']['failed_data_path']=data_path.relative_to(root).as_posix()
    data['batch_info']['failed_qc_path']=qc_path.relative_to(root).as_posix()
    data['batch_info']['latest_updated']=False
    from src.qc.report import report as health_report
    report=health_report(data)
    atomic_write(data_path,encoded(data))
    atomic_write(qc_path,report.encode('utf-8'))
    return data_path.relative_to(root).as_posix(),qc_path.relative_to(root).as_posix()
