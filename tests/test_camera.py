import importlib.util
import json
import tempfile
import time
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from main import parse_args
from deskmind.session import Session
from deskmind.vision import Detection
from deskmind.ui import make_server

@unittest.skipUnless(importlib.util.find_spec('cv2'), 'Camera integration requires installed OpenCV')
class CameraTests(unittest.TestCase):
    def test_browser_frames_run_detection_and_use_separate_memory(self):
        import cv2
        import numpy as np
        with tempfile.TemporaryDirectory() as tmp:
            session = Session(parse_args(['--demo','--db',str(Path(tmp)/'demo.db')]))
            session.start()
            server = make_server(session, 0)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            base=f'http://127.0.0.1:{server.server_port}'
            def post(route, body, content='application/json', origin=None):
                headers={'Content-Type':content,'X-DeskMind':'1'}
                if origin: headers['Origin']=origin
                return urlopen(Request(base+route, data=body, headers=headers), timeout=10)
            class Detector:
                def __init__(self, *args): pass
                def detect(self, frame):
                    self_test.assertEqual(frame.shape, (240,320,3))
                    return [Detection('bottle',.93,(.1,.4,.2,.7))]
            self_test=self
            try:
                time.sleep(.5)
                self.assertTrue(session.snapshot()['objects'])
                with patch('deskmind.runtime.YoloBackend', Detector):
                    with post('/api/source',b'{"source":"browser"}') as r:
                        self.assertEqual(json.load(r)['source'],'browser')
                    self.assertEqual(session.snapshot()['objects'], [])
                    ok, jpg=cv2.imencode('.jpg',np.zeros((240,320,3),dtype=np.uint8))
                    for i in range(4):
                        with post('/api/camera/frame',jpg.tobytes(),'image/jpeg') as r:
                            self.assertEqual(r.status,202)
                        time.sleep(.18)
                    deadline=time.monotonic()+3
                    while not session.snapshot()['objects'] and time.monotonic()<deadline: time.sleep(.05)
                    state=session.snapshot()
                    self.assertEqual(state['status'],'running')
                    self.assertEqual([o['label'] for o in state['objects']], ['bottle'])
                    image, mime=session.frame()
                    self.assertEqual(mime,'image/jpeg'); self.assertTrue(image.startswith(b'\xff\xd8'))
                    self.assertIn('middle-left',session.ask('Where is my bottle?'))
                    # Lost camera delivery pauses observation, without inventing absence.
                    with session.runtime.lock: session.runtime.last_observation=time.time()-6
                    time.sleep(.6)
                    self.assertTrue(session.snapshot()['stale'])
                    with post('/api/camera/frame',jpg.tobytes(),'image/jpeg'): pass
                    time.sleep(.2)
                    self.assertEqual(session.runtime.memory.events(kind='disappeared'), [])
                    self.assertGreaterEqual(len(session.runtime.memory.events(kind='observation_gap')),2)
                with post('/api/source',b'{"source":"stop"}') as r:
                    self.assertEqual(json.load(r)['status'],'paused')
                with self.assertRaises(HTTPError) as e:
                    post('/api/camera/frame',jpg.tobytes(),'image/jpeg')
                self.assertEqual(e.exception.code,409); e.exception.close()
                with self.assertRaises(HTTPError) as e:
                    post('/api/source',b'{"source":"demo"}',origin='https://example.com')
                self.assertEqual(e.exception.code,403); e.exception.close()
                with post('/api/source',b'{"source":"demo"}') as r:
                    self.assertEqual(json.load(r)['source'],'demo')
                self.assertTrue(session.snapshot()['objects'])
            finally:
                server.shutdown();server.server_close();session.close()
