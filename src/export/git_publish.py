import os
import subprocess
from pathlib import Path
from .security import scan_text

ALLOWED = ('.gitignore', 'README.md', 'requirements.txt', 'build_validation_batch.py',
           'scripts', 'src', 'config', 'tests', 'validation_packets', 'database/exports')


def git(root, *args, check=True):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', env=env, timeout=60)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def publish_git(root, info, settings):
    sha = None
    try:
        if git(root, 'branch', '--show-current').stdout.strip() != settings['git_branch']:
            raise RuntimeError('Wrong branch; expected main')
        if git(root, 'remote', 'get-url', settings['git_remote']).stdout.strip() != settings['git_url']:
            raise RuntimeError('Unexpected remote URL')
        # Refuse to sweep unrelated pre-staged files into this publication.
        if git(root, 'diff', '--cached', '--name-only').stdout.strip():
            raise RuntimeError('Existing staged changes; refusing to mix user staging with batch commit')
        paths = [p for p in ALLOWED if (root / p).exists()]
        for base in paths:
            path = root / base
            for file in ([path] if path.is_file() else path.rglob('*')):
                if not file.is_file() or '__pycache__' in file.parts:
                    continue
                if file.suffix in ('.json', '.md', '.csv') and scan_text(file.read_text(encoding='utf-8')):
                    raise RuntimeError(f'Secret/path scan blocked: {file.relative_to(root)}')
        git(root, 'add', '--', *paths)
        staged = git(root, 'diff', '--cached', '--name-only').stdout.splitlines()
        for name in staged:
            p = Path(name)
            if p.suffix in ('.xlsx','.xls','.db','.token','.secret') or '.env' in p.name:
                raise RuntimeError(f'Forbidden staged file: {name}')
            text = git(root, 'show', ':' + name).stdout
            # Source code contains scan patterns; literal real secrets remain detectable.
            from .security import SECRET
            if SECRET.search(text):
                raise RuntimeError(f'Secret in staged blob: {name}')
        changed = bool(staged)
        if changed:
            git(root, 'commit', '-m', f"validation: {info['batch_date']} {info['match_count']} matches")
        validation_sha = git(root, 'rev-parse', 'HEAD').stdout.strip()
        from src.health.history import record_commit
        if record_commit(root,info['source_content_hash'],validation_sha):
            git(root,'add','--','validation_packets/history_index.json')
            git(root,'commit','-m',f"validation-index: {info['batch_date']} {validation_sha[:12]}")
        sha = git(root, 'rev-parse', 'HEAD').stdout.strip()
        # Retry unsent local commits on unchanged runs; never falsely report a previous failed push as synced.
        git(root, 'push', settings['git_remote'], settings['git_branch'])
        remote = git(root, 'ls-remote', settings['git_remote'], 'refs/heads/' + settings['git_branch']).stdout.split()
        if not remote or remote[0] != sha:
            raise RuntimeError('Remote HEAD verification failed after push')
        return dict(status='PUSH_SUCCESS', changes='COMMITTED' if changed else 'NO_CHANGES', commit=sha,
                    validation_commit=validation_sha)
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
        return dict(status='PUSH_FAILED', commit=sha, error=str(exc))
