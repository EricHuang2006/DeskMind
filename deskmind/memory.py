"""SQLite state and event history; read/write operations are serialized."""
import json
import sqlite3
import threading
from pathlib import Path

class Memory:
    def __init__(self, path):
        if str(path) != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY, label TEXT NOT NULL, present INTEGER NOT NULL,
                first_seen REAL NOT NULL, last_seen REAL NOT NULL, present_since REAL NOT NULL,
                zone TEXT NOT NULL, bbox TEXT NOT NULL, last_interaction REAL,
                confidence REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL NOT NULL,
                type TEXT NOT NULL, object_id INTEGER, label TEXT, zone TEXT,
                detail TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS events_time ON events(timestamp);
            CREATE INDEX IF NOT EXISTS events_object ON events(object_id, timestamp);
        ''')
        self.db.commit()

    def objects(self):
        with self.lock:
            rows = [dict(r) for r in self.db.execute('SELECT * FROM objects ORDER BY id')]
        for r in rows:
            r['present'] = bool(r['present'])
            r['bbox'] = json.loads(r['bbox'])
        return rows

    def save(self, tracks, events):
        with self.lock, self.db:
            for t in tracks:
                self.db.execute('''INSERT INTO objects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET present=excluded.present,
                    last_seen=excluded.last_seen, present_since=excluded.present_since,
                    zone=excluded.zone, bbox=excluded.bbox,
                    last_interaction=excluded.last_interaction, confidence=excluded.confidence''',
                    (t.id, t.label, int(t.present), t.first_seen, t.last_seen, t.present_since,
                     t.zone, json.dumps(t.bbox), t.last_interaction, t.confidence))
            for e in events:
                self.db.execute('INSERT INTO events(timestamp,type,object_id,label,zone,detail) VALUES (?,?,?,?,?,?)',
                                (e['timestamp'], e['type'], e.get('object_id'), e.get('label'),
                                 e.get('zone'), e['detail']))

    def events(self, limit=40, since=None, kind=None):
        clauses, params = [], []
        if since is not None:
            clauses.append('timestamp >= ?'); params.append(since)
        if kind is not None:
            clauses.append('type = ?'); params.append(kind)
        where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
        params.append(limit)
        with self.lock:
            return [dict(r) for r in self.db.execute(
                'SELECT * FROM events' + where + ' ORDER BY timestamp DESC, id DESC LIMIT ?', params)]

    def begin_session(self, now):
        # The time offline is unknown: do not invent disappearance events.
        with self.lock, self.db:
            self.db.execute('UPDATE objects SET present = 0')
            self.db.execute('INSERT INTO events(timestamp,type,detail) VALUES (?,?,?)',
                            (now, 'observation_gap', 'New observation session; presence must be reconfirmed. Offline time is unknown.'))

    def close(self):
        with self.lock:
            self.db.close()
