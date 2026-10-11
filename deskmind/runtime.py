"""Single observation worker, synchronized snapshots, no storage of camera frames."""
import html
import logging
import os
import queue
from pathlib import Path
import threading
import time
from .vision import DemoBackend, YoloBackend
from .simulator import ManualSimulator
from .memory import Memory
from .tracker import Tracker
from .rules import RuleEngine
from .assistant import Assistant

LOG = logging.getLogger('deskmind')

class Runtime:
    def __init__(self, args):
        self.args = args
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.memory = Memory(args.db)
        self.memory.begin_session(time.time())
        self.tracker = Tracker(self.memory.objects(), confirm_frames=args.confirm_frames,
                               disappear_seconds=args.disappear_seconds)
        self.rules = RuleEngine(args.hydration_seconds, args.roi, args.monitored)
        self.simulator = ManualSimulator() if args.demo and not getattr(args, 'auto_demo', False) else None
        if self.simulator:
            self.rules.hydration_enabled = False
        self.assistant = Assistant(self.memory)
        self.status = 'starting'
        self.error = None
        self.last_observation = None
        self.fps = 0
        self.image = None
        self.image_type = 'image/svg+xml' if args.demo else 'image/jpeg'
        self.browser_camera = getattr(args, 'browser_camera', False)
        self.frames = queue.Queue(maxsize=1)
        self.thread = threading.Thread(target=self.run, name='observations', daemon=True)

    def start(self):
        self.thread.start()

    def snapshot(self):
        with self.lock:
            age = None if self.last_observation is None else max(0, time.time() - self.last_observation)
            return dict(mode='SIMULATED detections — no webcam or YOLO' if self.args.demo else ('LIVE browser camera / local YOLO — no UGen300' if self.browser_camera else 'Laptop webcam / YOLO — no UGen300'),
                        simulator=self.simulator_state(),
                        source='demo' if self.args.demo else ('browser' if self.browser_camera else 'webcam'),
                        status=self.status, error=self.error, observation_age_seconds=age,
                        stale=age is None or age > 5 or self.status != 'running',
                        fps=round(self.fps, 1), objects=self.memory.objects(),
                        events=self.memory.events(), warnings=list(self.rules.active.values()))

    def simulator_state(self):
        if not self.simulator:
            return None
        state = self.simulator.snapshot()
        remaining = None
        if self.rules.hydration_enabled:
            bottles = [t for t in self.tracker.tracks.values() if t.confirmed and t.present and t.label == 'bottle']
            if bottles:
                t = bottles[0]
                baseline = max(t.present_since, t.last_interaction if t.last_interaction is not None else t.present_since,
                               self.rules.hydration_not_before or t.present_since)
                remaining = max(0, self.rules.hydration_seconds - (time.time() - baseline))
        state.update(hydration_enabled=self.rules.hydration_enabled, hydration_remaining=remaining,
                     hydration_seconds=self.rules.hydration_seconds)
        return state

    def simulator_action(self, name):
        with self.lock:
            if not self.simulator or self.stop.is_set():
                raise RuntimeError('Select manual simulation before using these controls.')
            self.simulator.action(name)
            if name == 'hydration_start':
                self.rules.hydration_seconds = 8
                self.rules.hydration_not_before = time.time()
                self.rules.hydration_enabled = True
            elif name == 'reset':
                self.rules.hydration_enabled = False
                self.rules.hydration_not_before = None
            return self.simulator_state()

    def ask(self, question):
        with self.lock:
            answer = self.assistant.ask(question, time.time())
            if self.status != 'running' or self.last_observation is None or time.time() - self.last_observation > 5:
                answer = 'Observation is paused or stale. These are stored last observations, not current presence.\n' + answer
            return answer

    def process(self, detections, now):
        with self.lock:
            tracks, events = self.tracker.update(detections, now)
            _, warning_events = self.rules.evaluate(tracks, events, now)
            self.memory.save(tracks, events + warning_events)
            self.last_observation = now
            for e in events + warning_events:
                LOG.info('%s #%s %s: %s', e['label'], e['object_id'], e['type'], e['detail'])

    def demo_image(self, detections, elapsed):
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="600" viewBox="0 0 960 600">',
                 '<rect width="960" height="600" fill="#192838"/>',
                 '<text x="20" y="30" fill="#ffcd69" font-size="20">SIMULATION — scripted boxes, not camera inference</text>']
        for x in (320, 640):
            parts.append(f'<path d="M{x} 45V600" stroke="#415364" stroke-dasharray="6 6"/>')
        for y in (200, 400):
            parts.append(f'<path d="M0 {y}H960" stroke="#415364" stroke-dasharray="6 6"/>')
        for d in detections:
            x1, y1, x2, y2 = d.bbox
            color = '#ffbd69' if d.label in ('cat', 'dog') else '#62e4c8'
            parts.append(f'<rect x="{x1*960}" y="{y1*600}" width="{(x2-x1)*960}" height="{(y2-y1)*600}" fill="{color}" fill-opacity=".15" stroke="{color}" stroke-width="3"/>')
            parts.append(f'<text x="{x1*960}" y="{y1*600-8}" fill="{color}" font-size="18">{html.escape(d.label)} {d.confidence:.0%}</text>')
        x1,y1,x2,y2 = self.args.roi
        parts.append(f'<rect x="{x1*960}" y="{y1*600}" width="{(x2-x1)*960}" height="{(y2-y1)*600}" fill="none" stroke="#ffbd69" stroke-dasharray="12 8"/>')
        caption = 'MANUAL simulation — scene changes only with your controls' if self.simulator else f'Automatic scenario {elapsed % 40:.1f}s / 40s'
        parts.append(f'<text x="20" y="580" fill="white" font-size="18">{caption}</text></svg>')
        return ''.join(parts).encode()

    def camera_image(self, cv2, frame, detections):
        frame = frame.copy()
        h, w = frame.shape[:2]
        for d in detections:
            x1,y1,x2,y2 = d.bbox
            p1, p2 = (int(x1*w), int(y1*h)), (int(x2*w), int(y2*h))
            cv2.rectangle(frame, p1, p2, (100, 230, 170), 2)
            cv2.putText(frame, f'{d.label} {d.confidence:.0%}', (p1[0], max(20, p1[1]-8)), cv2.FONT_HERSHEY_SIMPLEX, .6, (100,230,170), 2)
        x1,y1,x2,y2 = self.args.roi
        cv2.rectangle(frame, (int(x1*w),int(y1*h)), (int(x2*w),int(y2*h)), (0,190,255), 2)
        cv2.putText(frame, 'LAPTOP PROTOTYPE / YOLO', (15, 25), cv2.FONT_HERSHEY_SIMPLEX, .7, (0,190,255), 2)
        ok, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ok:
            raise RuntimeError('Could not encode camera frame')
        return encoded.tobytes()

    def frame(self):
        with self.lock:
            return self.image, self.image_type

    def submit_frame(self, data):
        if not self.browser_camera or self.stop.is_set() or self.status == 'error':
            raise RuntimeError('Start live camera before sending frames.')
        try:
            self.frames.put_nowait(data)
        except queue.Full:
            try:
                self.frames.get_nowait()
            except queue.Empty:
                pass
            try:
                self.frames.put_nowait(data)
            except queue.Full:
                pass

    def run(self):
        cap = None
        try:
            if self.args.demo:
                backend = self.simulator or DemoBackend()
            else:
                try:
                    import cv2
                except ImportError as exc:
                    raise RuntimeError('Install webcam dependencies with pip install -r requirements.txt') from exc
                os.environ.setdefault('YOLO_CONFIG_DIR', str(Path(self.args.db).resolve().parent / '.ultralytics'))
                backend = YoloBackend(self.args.model, self.args.confidence, self.args.device, self.args.image_size)
                if not self.browser_camera:
                    cap = cv2.VideoCapture(self.args.camera)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    if not cap.isOpened():
                        raise RuntimeError(f'Cannot open camera {self.args.camera}. Check camera permissions / index, or use Start live camera in the browser.')
                else:
                    import numpy as np
                    with self.lock:
                        self.status = 'waiting for camera'
            start = time.monotonic()
            while not self.stop.is_set():
                tick = time.monotonic()
                if self.args.demo:
                    frame = tick - start
                elif self.browser_camera:
                    try:
                        data = self.frames.get(timeout=.5)
                    except queue.Empty:
                        with self.lock:
                            if self.last_observation is not None and time.time() - self.last_observation > 5:
                                self.status = 'paused'
                        continue
                    frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is None or frame.shape[0] > 1080 or frame.shape[1] > 1920:
                        LOG.warning('Rejected invalid or oversized browser camera frame')
                        continue
                    if self.last_observation is not None and time.time() - self.last_observation > 5:
                        with self.lock:
                            self.memory.begin_session(time.time())
                            self.tracker = Tracker(self.memory.objects(), confirm_frames=self.args.confirm_frames, disappear_seconds=self.args.disappear_seconds)
                            self.rules = RuleEngine(self.args.hydration_seconds, self.args.roi, self.args.monitored)
                else:
                    ok, frame = cap.read()
                    if not ok:
                        raise RuntimeError('Camera read failed; observation paused. No disappearances inferred from this failure.')
                detections = backend.detect(frame)
                now = time.time()
                self.process(detections, now)
                image = self.demo_image(detections, frame) if self.args.demo else self.camera_image(cv2, frame, detections)
                elapsed = time.monotonic() - tick
                with self.lock:
                    self.image = image
                    self.fps = 1 / max(1 / self.args.max_fps, elapsed)
                    self.status = 'running'
                self.stop.wait(max(0, 1 / self.args.max_fps - elapsed))
        except Exception as exc:
            LOG.exception('Observation stopped')
            with self.lock:
                self.status, self.error = 'error', str(exc)
        finally:
            if cap is not None:
                cap.release()
            with self.lock:
                if self.status != 'error':
                    self.status = 'stopped'

    def close(self):
        self.stop.set()
        if self.thread.ident is not None:
            self.thread.join(timeout=10)
        if not self.thread.is_alive():
            self.memory.close()
        else:
            LOG.warning('Observation is still blocked; process exit will stop the worker.')
