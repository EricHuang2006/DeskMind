import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen, quote
from main import parse_args
from deskmind.runtime import Runtime
from deskmind.ui import make_server

class HttpTests(unittest.TestCase):
    def test_running_dashboard_frames_queries_and_persistent_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Runtime(parse_args(['--demo','--db',str(Path(tmp)/'demo.db')]))
            server = make_server(runtime, 0)
            serving = threading.Thread(target=server.serve_forever, daemon=True)
            serving.start(); runtime.start()
            base = f'http://127.0.0.1:{server.server_port}'
            try:
                deadline = time.monotonic()+5
                while not runtime.memory.objects() and time.monotonic()<deadline:
                    runtime.stop.wait(.05)
                with urlopen(base+'/') as r:
                    self.assertIn(b'Ask workspace memory', r.read())
                with urlopen(base+'/api/state') as r:
                    state = json.load(r)
                    self.assertIn('SIMULATED', state['mode'])
                    self.assertEqual(state['status'], 'running')
                    self.assertFalse(state['stale'])
                    self.assertGreaterEqual(len(state['objects']), 3)
                with urlopen(base+'/api/frame') as r:
                    self.assertEqual(r.headers['Content-Type'], 'image/svg+xml')
                    self.assertIn(b'SIMULATION', r.read())
                with urlopen(base+'/api/query?q='+quote('Where is my bottle?')) as r:
                    self.assertIn('middle-left', json.load(r)['answer'])
                for route in ('/not-found', '/api/query?q='+'a'*501):
                    with self.assertRaises(HTTPError) as caught:
                        urlopen(base+route)
                    caught.exception.close()
            finally:
                server.shutdown(); server.server_close(); runtime.close(); serving.join(2)
