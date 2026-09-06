import math
import re
from datetime import datetime, timedelta, timezone


def identifier(value):
    if value is None or value == '':
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def timestamp(value, anchor, offset=8):
    if not value:
        return None
    s = str(value).strip()
    try:
        if re.fullmatch(r'\d{1,2}-\d{1,2} \d{2}:\d{2}(?::\d{2})?', s):
            # Choose closest calendar year around the source anchor (New Year safe).
            base = datetime.fromisoformat(anchor.replace('Z', '+00:00'))
            choices = []
            for year in (base.year - 1, base.year, base.year + 1):
                try:
                    dt = datetime.fromisoformat(f'{year}-{s.split()[0].split("-")[0].zfill(2)}-{s.split()[0].split("-")[1].zfill(2)}T{s.split()[1]}')
                    choices.append(dt)
                except ValueError:
                    pass
            dt = min(choices, key=lambda d: abs((d - base.replace(tzinfo=None)).total_seconds()))
        elif ',' in s:
            parts = s.split(',')
            if len(parts) != 6:
                return None
            month = int(parts[1][:-2]) - 1 if parts[1].endswith('-1') else int(parts[1])
            dt = datetime(int(parts[0]), month + 1, *map(int, parts[2:]))
        else:
            dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            if offset is None:
                return None
            dt = dt.replace(tzinfo=timezone(timedelta(hours=offset)))
        return dt.astimezone(timezone.utc).isoformat(timespec='seconds')
    except (ValueError, TypeError, OverflowError):
        return None


LINES = {'平手': 0, '平': 0, '半球': .5, '一球': 1, '球半': 1.5, '一球半': 1.5,
         '两球': 2, '两球半': 2.5, '三球': 3, '三球半': 3.5, '四球': 4,
         '四球半': 4.5, '五球': 5, '五球半': 5.5, '六球': 6, '六球半': 6.5,
         '半': .5, '一': 1, '两': 2, '三': 3, '四': 4, '五': 5}


def line_value(raw, market):
    if raw is None:
        return None
    s = str(raw).strip()
    receiving = s.startswith('受')
    s = s.removeprefix('受让').removeprefix('受')
    parts = s.split('/')
    nums = [LINES.get(p, number(p)) for p in parts]
    if any(v is None for v in nums):
        return None
    line = sum(nums) / len(nums)
    # Chinese AH page labels describe home giving; numeric source signs retained.
    if market == 'ah' and any(c in s for c in '平半球一两三四五六'):
        return abs(line) if receiving else -abs(line)
    return line


def decimal_prices(values, fmt, maximum=10001):
    nums = [number(v) for v in values]
    if any(v is None for v in nums):
        return None, 'missing_or_non_numeric'
    if fmt == 'HK':
        if any(v <= 0 for v in nums):
            return None, 'impossible_hk_value'
        nums = [v + 1 for v in nums]
    elif fmt != 'DECIMAL':
        return None, 'unverified_odds_format'
    if any(v <= 1 or v > maximum for v in nums):
        return None, 'impossible_decimal_value'
    return nums, None
