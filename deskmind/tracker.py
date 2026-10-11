"""Greedy same-class spatial association with appearance/absence/movement debounce.
IDs are approximate local track IDs, not guaranteed physical identities.
"""
from dataclasses import dataclass
import math
from .vision import Detection

ROWS = ('top', 'middle', 'bottom')
COLS = ('left', 'center', 'right')

def zone(center):
    x, y = center
    return ROWS[min(2, int(y * 3))] + '-' + COLS[min(2, int(x * 3))]

def center(box):
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)

def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

@dataclass
class Track:
    id: int
    label: str
    present: bool
    first_seen: float
    last_seen: float
    present_since: float
    zone: str
    bbox: tuple
    last_interaction: float | None
    confidence: float
    hits: int = 0
    confirmed: bool = False
    move_hits: int = 0
    anchor: tuple = (0, 0)
    target: tuple | None = None

class Tracker:
    def __init__(self, saved=(), confirm_frames=3, disappear_seconds=2.0,
                 move_frames=3, move_distance=.08, match_distance=.7, reidentify_seconds=300):
        self.confirm_frames = confirm_frames
        self.disappear_seconds = disappear_seconds
        self.move_frames, self.move_distance = move_frames, move_distance
        self.match_distance, self.reidentify_seconds = match_distance, reidentify_seconds
        self.tracks = {}
        for row in saved:
            t = Track(**row, confirmed=True, anchor=center(row['bbox']))
            self.tracks[t.id] = t
        self.next_id = max(self.tracks, default=0) + 1
        self.last_update = None

    @staticmethod
    def event(t, now, kind, detail):
        return dict(timestamp=now, type=kind, object_id=t.id, label=t.label, zone=t.zone, detail=detail)

    def update(self, detections: list[Detection], now: float):
        if self.last_update is not None and now < self.last_update:
            raise ValueError('Observation timestamps must be nondecreasing')
        self.last_update = now
        events, assignments = [], {}
        pairs = []
        for t in self.tracks.values():
            if t.confirmed and not t.present and now - t.last_seen > self.reidentify_seconds:
                continue
            for i, d in enumerate(detections):
                if d.label == t.label:
                    dist = distance(center(t.bbox), d.center)
                    if dist <= self.match_distance:
                        # Prefer currently present tracks over historical absent candidates.
                        pairs.append((dist + (0 if t.present or not t.confirmed else .2), t.id, i))
        used = set()
        for _, tid, i in sorted(pairs):
            if tid not in assignments and i not in used:
                assignments[tid] = i; used.add(i)
        for i, d in enumerate(detections):
            if i not in used:
                t = Track(self.next_id, d.label, False, now, now, now, zone(d.center), d.bbox,
                          None, d.confidence, anchor=d.center)
                self.tracks[t.id] = t
                self.next_id += 1
                assignments[t.id] = i
        for tid, t in list(self.tracks.items()):
            if tid not in assignments:
                t.hits = 0; t.move_hits = 0; t.target = None
                if not t.confirmed:
                    del self.tracks[tid]
                elif t.present and now - t.last_seen >= self.disappear_seconds:
                    t.present = False
                    events.append(self.event(t, now, 'disappeared',
                        f'No detection for {self.disappear_seconds:g}s. Last observed at {t.last_seen:.3f} in {t.zone}; removal vs occlusion is unknown.'))
                continue
            d = detections[assignments[tid]]
            t.hits += 1; t.last_seen = now; t.confidence = d.confidence
            t.bbox = tuple(.6 * a + .4 * b for a, b in zip(t.bbox, d.bbox))
            if not t.present:
                if t.hits >= self.confirm_frames:
                    t.present = True; t.confirmed = True; t.present_since = now
                    t.zone = zone(d.center); t.anchor = d.center; t.bbox = d.bbox
                    events.append(self.event(t, now, 'appeared', 'Presence confirmed by consecutive observations.'))
                continue
            # Movement must stay near a new location for consecutive observations.
            if distance(d.center, t.anchor) >= self.move_distance:
                if t.target is not None and distance(d.center, t.target) <= self.move_distance / 2:
                    t.move_hits += 1
                else:
                    t.target = d.center; t.move_hits = 1
                if t.move_hits >= self.move_frames:
                    old_zone = t.zone
                    t.zone = zone(d.center); t.anchor = d.center
                    t.move_hits = 0; t.target = None; t.last_interaction = now
                    events.append(self.event(t, now, 'moved', f'Observed position changed from {old_zone} to {t.zone}.'))
                    events.append(self.event(t, now, 'interaction', 'Interaction inferred from sustained object movement; no drinking or human contact is proven.'))
            else:
                t.move_hits = 0; t.target = None
        return [t for t in self.tracks.values() if t.confirmed], events
