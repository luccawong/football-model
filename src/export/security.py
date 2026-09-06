import re
from pathlib import PureWindowsPath

SENSITIVE_KEY = re.compile(r'(^|[_\W])(password|passwd|token|cookie|session|authorization|api_key|api_secret|secret|credentials)([_\W]|$)', re.I)
SECRET = re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._-]{15,})')
# A drive path has one separator after ``C:``. Exclude URI schemes such as
# ``https://`` (where the first slash is immediately followed by another).
PATH = re.compile(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/](?![\\/])[^\r\n\"<>|]*')


def sanitize(value, audit, location='root'):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if SENSITIVE_KEY.search(str(key)) and item not in (None, ''):
                result[key] = '[REDACTED]'
                audit.append(location + '.' + key)
            else:
                result[key] = sanitize(item, audit, location + '.' + key)
        return result
    if isinstance(value, list):
        return [sanitize(v, audit, f'{location}[{i}]') for i,v in enumerate(value)]
    if isinstance(value, str):
        new = SECRET.sub('[REDACTED]', value)
        new = re.sub(r'(?i)(token|password|cookie|session|api_key|secret)=([^\s&]+)', r'\1=[REDACTED]', new)
        new = PATH.sub(lambda m: '[LOCAL_PATH]/' + PureWindowsPath(m[0]).name, new)
        new = re.sub(r'/(?:Users|home)/[^\s"<>]+', '[LOCAL_PATH]', new)
        if new != value:
            audit.append(location)
        return new
    return value


def scan_text(text):
    return bool(SECRET.search(text) or re.search(r'[A-Za-z]:[\\/]Users[\\/]', text)
                or re.search(r'(?i)(password|token|api_key|cookie|session)\s*[:=]\s*["\']?(?!\[REDACTED\])[^\s"\',}]{12,}', text))
