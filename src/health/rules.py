from dataclasses import asdict, dataclass, field


LEVEL = {'INFO': 0, 'WARN': 1, 'FAIL': 2}


@dataclass(frozen=True)
class HealthEvent:
    code: str
    severity: str
    message: str
    match_ids: tuple[str, ...] = field(default_factory=tuple)
    details: dict = field(default_factory=dict)

    def as_dict(self):
        value = asdict(self)
        value['match_ids'] = list(self.match_ids)
        return value


class RuleEngine:
    """Small declarative aggregator; detectors emit facts, this engine owns status."""

    def __init__(self, warning_count_pass_max=0):
        self.warning_count_pass_max = warning_count_pass_max

    def evaluate(self, events):
        unique = {}
        for event in events:
            key = (event.code, event.match_ids, repr(sorted(event.details.items())))
            old = unique.get(key)
            if old is None or LEVEL[event.severity] > LEVEL[old.severity]:
                unique[key] = event
        ordered = sorted(unique.values(), key=lambda e: (-LEVEL[e.severity], e.code, e.match_ids))
        fails = [e for e in ordered if e.severity == 'FAIL']
        warnings = [e for e in ordered if e.severity == 'WARN']
        status = 'FAIL' if fails else 'WARN' if len(warnings) > self.warning_count_pass_max else 'PASS'
        return {'status': status, 'warning_count': len(warnings), 'critical_error_count': len(fails),
                'events': [e.as_dict() for e in ordered],
                'reason_codes': [e.code for e in fails] if fails else [e.code for e in warnings]}
