"""Deterministic assistance, based solely on observation."""
class RuleEngine:
    def __init__(self, hydration_seconds=1800, roi=(0, 0, 1, 1), monitored=('bottle', 'cell phone', 'book')):
        self.hydration_seconds, self.roi = hydration_seconds, roi
        self.monitored = set(monitored)
        self.hydration_enabled = True
        self.hydration_not_before = None
        self.active = {}
        self.missing = {}

    def evaluate(self, tracks, events, now):
        by_id = {t.id: t for t in tracks}
        for e in events:
            if e['type'] == 'disappeared' and e['label'] in self.monitored:
                t = by_id[e['object_id']]
                self.missing[t.id] = dict(key=f'missing:{t.id}', object_id=t.id, label=t.label,
                    message=f'{t.label} #{t.id} is no longer detected. Last observed in {t.zone}.', last_seen=t.last_seen)
            elif e['type'] == 'appeared':
                self.missing.pop(e['object_id'], None)
        active = {w['key']: w for w in self.missing.values()}
        x1, y1, x2, y2 = self.roi
        for t in tracks:
            if not t.present:
                continue
            cx, cy = (t.bbox[0] + t.bbox[2]) / 2, (t.bbox[1] + t.bbox[3]) / 2
            if t.label in ('cat', 'dog') and x1 <= cx <= x2 and y1 <= cy <= y2:
                key = f'pet:{t.id}'
                active[key] = dict(key=key, object_id=t.id, label=t.label,
                                  message=f'{t.label} #{t.id} detected inside the workspace ROI.')
            baseline = max(t.present_since, t.last_interaction if t.last_interaction is not None else t.present_since)
            if self.hydration_not_before is not None:
                baseline = max(baseline, self.hydration_not_before)
            if self.hydration_enabled and t.label == 'bottle' and now - baseline >= self.hydration_seconds:
                key = f'hydration:{t.id}'
                active[key] = dict(key=key, object_id=t.id, label=t.label,
                    message=f'Hydration reminder: no observed bottle movement for {self.hydration_seconds:g}s. Drinking is not measured.')
        warnings = []
        for key, warning in active.items():
            if key not in self.active:
                t = by_id[warning['object_id']]
                warnings.append(dict(timestamp=now, type='warning', object_id=t.id, label=t.label,
                                     zone=t.zone, detail=warning['message']))
        self.active = active
        return list(active.values()), warnings
