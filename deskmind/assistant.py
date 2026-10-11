"""Read-only deterministic history queries. No generative model or cloud service."""
from datetime import datetime, timezone
import re
from .vision import CLASSES

ALIASES = {'cellphone': 'cell phone', 'phone': 'cell phone', 'mobile': 'cell phone',
           'water bottle': 'bottle', 'mug': 'cup'}

def stamp(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat(timespec='seconds')

class Assistant:
    def __init__(self, memory):
        self.memory = memory

    def ask(self, query, now):
        q = re.sub(r'[^a-z0-9 ]', '', query.lower())
        if 'disappear' in q or 'missing' in q:
            events = self.memory.events(limit=12, kind='disappeared')
            if not events:
                return 'No disappearances have been recorded.'
            return '\n'.join(f"{e['label']} #{e['object_id']}: no longer detected at {stamp(e['timestamp'])}; last zone {e['zone']}." for e in events)
        if 'change' in q or 'recent' in q:
            events = [e for e in self.memory.events(limit=80, since=now - 300)
                      if e['type'] in ('appeared', 'disappeared', 'moved', 'interaction')][:12]
            return '\n'.join(f"{stamp(e['timestamp'])} · {e['label']} #{e['object_id']} · {e['type']} · {e['zone']}" for e in events) or 'No object changes recorded in the last five minutes.'
        words = set(q.split())
        label = next((v for k, v in ALIASES.items() if re.search(r'\b' + re.escape(k) + r'\b', q)), None)
        if label is None:
            label = next((c for c in sorted(CLASSES) if set(c.split()) <= words), None)
        if label and ('where' in words or 'when' in words or 'last' in words):
            items = sorted((r for r in self.memory.objects() if r['label'] == label), key=lambda r: r['last_seen'], reverse=True)
            if not items:
                return f'I have never observed a {label} in this database.'
            return '\n'.join(f"{label} #{r['id']}: {'present (recently detected)' if r['present'] else 'not currently detected'}. Last observed in {r['zone']} at {stamp(r['last_seen'])}." for r in items[:8])
        return 'Try: Where is my bottle? When was my phone last seen? What disappeared? What changed recently? Supported objects: bottle, cup, laptop, keyboard, mouse, phone, book, cat, dog.'
