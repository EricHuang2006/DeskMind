from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from deskmind.vision import Detection, DemoBackend, HailoBackend, YoloBackend
from deskmind.tracker import Tracker
from deskmind.memory import Memory
from deskmind.rules import RuleEngine
from deskmind.assistant import Assistant
from deskmind.runtime import Runtime
from main import parse_args

def detection(label='bottle', x=.1, y=.4):
    return Detection(label, .9, (x, y, x+.08, y+.15))

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory(':memory:')
        self.tracker = Tracker(confirm_frames=3, disappear_seconds=2)
        self.rules = RuleEngine(hydration_seconds=10)
        self.warnings = []
    def tearDown(self): self.memory.close()
    def step(self, detections, now):
        tracks, events = self.tracker.update(detections, now)
        self.warnings, warnings = self.rules.evaluate(tracks, events, now)
        self.memory.save(tracks, events+warnings)
        return events
    def appear(self, d=None, start=0):
        for dt in (0,.2,.4): self.step([d or detection()], start+dt)

    def test_flicker_does_not_create_objects_or_spam_disappearances(self):
        self.step([detection()], 0); self.step([], .2)
        self.assertEqual(self.memory.objects(), [])
        self.appear(start=1); self.step([], 1.6); self.step([detection()], 1.8)
        self.assertTrue(self.memory.objects()[0]['present'])
        self.step([], 3.9); self.step([], 5)
        self.assertEqual([e['type'] for e in self.memory.events()], ['warning','disappeared','appeared'])
        self.assertEqual(self.memory.objects()[0]['last_seen'], 1.8)
        self.assertIn('Last observed', self.warnings[0]['message'])

    def test_motion_is_debounced_and_resets_hydration(self):
        self.appear(); self.step([detection()], 10.5); self.step([detection()], 11)
        self.assertEqual(len(self.memory.events(kind='warning')), 1)
        self.assertIn('Drinking is not measured', self.warnings[0]['message'])
        self.step([detection(x=.7)], 12); self.step([detection()], 12.2)
        self.assertEqual(self.memory.events(kind='moved'), [])
        for t in (13,13.2,13.4): self.step([detection(x=.7)], t)
        self.assertEqual(len(self.memory.objects()), 1)
        self.assertEqual(self.memory.objects()[0]['zone'], 'middle-right')
        self.assertEqual(self.memory.objects()[0]['last_interaction'], 13.4)
        self.assertEqual(len(self.memory.events(kind='interaction')), 1)
        self.assertEqual(self.warnings, [])

    def test_boundary_jitter_does_not_count_as_interaction(self):
        self.appear(detection(x=.29))
        for i in range(20): self.step([detection(x=.29 + .008*(i%2))], 1+i*.2)
        self.assertEqual(self.memory.events(kind='interaction'), [])

    def test_identical_objects_are_stored_separately(self):
        for t in (0,.2,.4): self.step([detection(x=.1),detection(x=.7)], t)
        self.step([detection(x=.7)], 3)
        rows = self.memory.objects()
        self.assertEqual(len(rows), 2)
        self.assertFalse(rows[0]['present']); self.assertTrue(rows[1]['present'])
        answer = Assistant(self.memory).ask('Where is my bottle?', 3)
        self.assertIn('bottle #1', answer); self.assertIn('bottle #2', answer)

    def test_reappearance_keeps_id_and_clears_missing(self):
        self.appear(); self.step([], 3)
        self.assertTrue(self.warnings)
        for t in (4,4.2,4.4): self.step([detection()], t)
        self.assertEqual(len(self.memory.objects()), 1)
        self.assertEqual(self.memory.objects()[0]['first_seen'], 0)
        self.assertEqual(self.warnings, [])
        self.assertEqual(len(self.memory.events(kind='appeared')), 2)

    def test_pet_roi_and_warning_deduplication(self):
        self.rules = RuleEngine(roi=(.3,.3,.9,.9))
        self.appear(detection('cat', .1)); self.assertEqual(self.warnings, [])
        for t in (1,1.2,1.4,1.6,1.8,2): self.step([detection('cat', .5)], t)
        self.assertTrue(self.warnings)
        self.assertEqual(len(self.memory.events(kind='warning')), 1)
        self.step([], 5); self.assertEqual(self.warnings, [])

    def test_queries_are_grounded(self):
        a = Assistant(self.memory)
        self.assertIn('never observed', a.ask('Where is my bottle?', 1))
        self.assertIn('Try:', a.ask('Delete the database', 1))
        self.appear(detection('cell phone')); self.step([], 3)
        self.assertIn('not currently detected', a.ask('When was my phone last seen?', 4))
        self.assertIn('1970-01-01T00:00:00', a.ask('When was my phone last seen?', 4))
        self.assertIn('cell phone #1', a.ask('What disappeared?', 4))
        self.assertIn('disappeared', a.ask('What changed recently?', 4))
        self.assertIn('No object changes', a.ask('What changed recently?', 1000))

    def test_persistence_and_restart_do_not_invent_disappearances(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = Memory(Path(tmp)/'memory.db'); self.appear()
            m.save(list(self.tracker.tracks.values()), self.memory.events()); m.close()
            m = Memory(Path(tmp)/'memory.db')
            self.assertTrue(m.objects()[0]['present'])
            m.begin_session(50)
            self.assertFalse(m.objects()[0]['present']); self.assertEqual(m.events(kind='disappeared'), [])
            tracker = Tracker(m.objects())
            for now in (50,50.2,50.4):
                tracks, events = tracker.update([detection()], now); m.save(tracks, events)
            self.assertTrue(m.objects()[0]['present']); self.assertEqual(m.objects()[0]['first_seen'], 0)
            m.close()

    def test_old_identity_is_not_reused_indefinitely(self):
        self.appear(); self.step([], 3); self.appear(start=400)
        self.assertEqual(len(self.memory.objects()), 2)

    def test_invalid_inputs_and_time(self):
        with self.assertRaises(ValueError): Detection('bottle', .9, (-.1,0,.2,.3))
        with self.assertRaises(ValueError): Detection('bottle', float('nan'), (0,0,.2,.3))
        self.step([], 3)
        with self.assertRaises(ValueError): self.step([], 2)
        for argv in (['--roi','0,0,0,1'],['--confidence','2'],['--hydration-seconds','nan'],['--confirm-frames','0']):
            with patch('sys.stderr'), self.assertRaises(SystemExit): parse_args(argv)
        with self.assertRaises(NotImplementedError): HailoBackend()

    def test_yolo_adapter_contract(self):
        class Tensor:
            def __init__(self, values): self.values = values
            def cpu(self): return self
            def tolist(self): return self.values
        boxes = SimpleNamespace(xyxyn=Tensor([[-.01,.2,.3,1.01],[.4,.4,.5,.5]]), cls=Tensor([0,1]), conf=Tensor([.9,.8]))
        class Model:
            def __init__(self, path): pass
            def predict(self, *args, **kwargs):
                return [SimpleNamespace(boxes=boxes, names={0:'bottle',1:'person'})]
        with patch.dict('sys.modules', {'ultralytics':SimpleNamespace(YOLO=Model)}): result = YoloBackend().detect(object())
        self.assertEqual(len(result), 1); self.assertIsInstance(result[0], Detection)
        self.assertEqual(result[0].bbox, (0,.2,.3,1))

    def test_complete_simulated_scenario(self):
        backend = DemoBackend()
        for i in range(200): self.step(backend.detect(i/5), i/5)
        kinds = {e['type'] for e in self.memory.events(limit=1000)}
        self.assertTrue({'appeared','disappeared','moved','interaction','warning'} <= kinds)
        self.assertGreaterEqual(len(self.memory.objects()), 4)

    def test_camera_failure_does_not_generate_disappearance(self):
        runtime = Runtime(parse_args(['--db',':memory:','--no-ui']))
        class Cap:
            def set(self, *args): pass
            def isOpened(self): return True
            def read(self): return False, None
            def release(self): pass
        cv = SimpleNamespace(VideoCapture=lambda index:Cap(), CAP_PROP_FRAME_WIDTH=1,CAP_PROP_FRAME_HEIGHT=2,CAP_PROP_BUFFERSIZE=3)
        with patch.dict('sys.modules', {'cv2':cv}), patch('deskmind.runtime.YoloBackend'), patch('deskmind.runtime.LOG'): runtime.run()
        self.assertEqual(runtime.status, 'error'); self.assertTrue(runtime.snapshot()['stale'])
        self.assertEqual(runtime.memory.events(kind='disappeared'), [])
        self.assertIn('paused or stale', runtime.ask('Where is my bottle?')); runtime.close()

if __name__ == '__main__': unittest.main()
