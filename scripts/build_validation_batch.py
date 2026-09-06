"""One command: Excel -> deterministic packet -> QC -> commit -> push."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.pipeline import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('excel_path')
    parser.add_argument('--dry-run',action='store_true',help='Generate and QC locally without commit or push')
    args = parser.parse_args()
    lock = ROOT / '.pipeline.lock'
    try:
        fd = os.open(lock, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:
        print(json.dumps(dict(status='BUILD_FAILED',error='Pipeline lock exists. Check active process before removing stale lock.')))
        return 1
    try:
        os.close(fd)
        result = run(args.excel_path,ROOT,args.dry_run)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        print('================================')
        print(f"BATCH STATUS: {result.get('batch_status','FAIL')}")
        if result.get('batch_status') == 'FAIL':
            print(f"Critical errors: {result.get('critical_error_count',1)}")
            print('Latest updated: NO')
            print('Valid GitHub batch changed: NO')
        else:
            print(f"Matches: {result.get('match_count',0)}/{result.get('match_count',0)}")
            print(f"Warnings: {result.get('warning_count',0)}")
            print(f"Latest updated: {'YES' if result.get('latest_updated') else 'NO'}")
            print(f"GitHub push: {'NOT RUN (DRY RUN)' if args.dry_run else 'SUCCESS' if result.get('status')=='PUSH_SUCCESS' else 'FAILED'}")
        print(f"QC: {result.get('qc_path','unavailable')}")
        print('================================')
        return 1 if result['status'] in ('PUSH_FAILED','QC_FAILED','STALE_SOURCE') else 0
    except Exception as exc:
        print(json.dumps(dict(status='BUILD_FAILED',error=str(exc)),ensure_ascii=False))
        return 1
    finally:
        lock.unlink(missing_ok=True)


if __name__=='__main__':
    raise SystemExit(main())
