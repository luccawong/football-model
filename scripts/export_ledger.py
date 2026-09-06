"""Read-only consistent SQLite snapshot; no database writes or migrations."""
import argparse
import csv
import io
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.export.files import atomic_write, encoded
from src.export.security import sanitize, scan_text


def export_ledger(path, root=ROOT):
    path=Path(path).resolve()
    connection=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
    connection.row_factory=sqlite3.Row
    tables={}
    try:
        connection.execute('BEGIN')
        names=[r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for name in names:
            quoted='"'+name.replace('"','""')+'"'
            tables[name]=[dict(r) for r in connection.execute('SELECT * FROM '+quoted)]
            tables[name].sort(key=lambda r:json.dumps(r,sort_keys=True,default=str))
    finally:
        connection.close()
    redactions=[]
    tables=sanitize(tables,redactions)
    snapshot=dict(schema_version='1.0',tables=tables,redactions=redactions)
    out=Path(root)/'database/exports'
    content=encoded(snapshot)
    if scan_text(content.decode()):
        raise ValueError('Security scan blocked ledger snapshot')
    csvfile=io.StringIO(newline='')
    writer=csv.writer(csvfile)
    writer.writerow(['table','record_json'])
    for name,rows in tables.items():
        for row in rows:
            writer.writerow([name,json.dumps(row,ensure_ascii=False,sort_keys=True)])
    atomic_write(out/'ledger_snapshot.json',content)
    atomic_write(out/'ledger_snapshot.csv',csvfile.getvalue().encode('utf-8-sig'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('database')
    args=p.parse_args()
    export_ledger(args.database)
