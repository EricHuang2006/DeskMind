import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from main import parse_args
from deskmind.runtime import Runtime
from deskmind.session import Session
from deskmind.ui import make_server

class SimulatorTests(unittest.TestCase):
    def test_manual_scene_waits_and_actions_use_real_memory_and_rules(self):
        runtime=Runtime(parse_args(['--demo','--db',':memory:']))
        def observe(now):
            with patch('deskmind.runtime.time.time',return_value=now):
                runtime.process(runtime.simulator.detect(now),now)
                return runtime.snapshot()
        try:
            for t in (1000,1000.2,1000.4): state=observe(t)
            initial=[(o['id'],o['label'],o['zone']) for o in state['objects']]
            state=observe(1100)
            self.assertEqual(initial,[(o['id'],o['label'],o['zone']) for o in state['objects']])
            self.assertFalse(state['warnings'])
            runtime.simulator_action('bottle_right')
            for t in (1101,1101.2,1101.4): state=observe(t)
            self.assertIn('middle-right',runtime.ask('Where is my bottle?'))
            self.assertEqual(len(runtime.memory.events(kind='moved')),1)
            self.assertEqual(len(runtime.memory.events(kind='interaction')),1)
            runtime.simulator_action('phone_hide');observe(1102);state=observe(1104)
            self.assertIn('not currently detected',runtime.ask('When was my phone last seen?'))
            self.assertTrue(any(w['key'].startswith('missing:') for w in state['warnings']))
            runtime.simulator_action('phone_show')
            for t in (1105,1105.2,1105.4): state=observe(t)
            self.assertFalse(any(w['key'].startswith('missing:') for w in state['warnings']))
            runtime.simulator_action('pet_show')
            for t in (1106,1106.2,1106.4): state=observe(t)
            self.assertTrue(any(w['key'].startswith('pet:') for w in state['warnings']))
            before=len(runtime.memory.events(kind='interaction'))
            with patch('deskmind.runtime.time.time',return_value=1107):
                runtime.simulator_action('hydration_start')
            state=observe(1114.9)
            self.assertFalse(any(w['key'].startswith('hydration:') for w in state['warnings']))
            state=observe(1115.1)
            self.assertTrue(any(w['key'].startswith('hydration:') for w in state['warnings']))
            self.assertEqual(before,len(runtime.memory.events(kind='interaction')))
            count=len(runtime.memory.events(limit=1000))
            runtime.simulator_action('reset')
            for t in (1116,1116.2,1116.4,1119): state=observe(t)
            self.assertFalse(state['warnings'])
            self.assertFalse(state['simulator']['hydration_enabled'])
            self.assertGreaterEqual(len(runtime.memory.events(limit=1000)),count)
            self.assertTrue(all(o['present'] for o in state['objects'] if o['label']!='cat'))
            with self.assertRaises(ValueError): runtime.simulator_action('invent_warning')
        finally: runtime.close()

    def test_simulator_controls_over_http_and_source_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            session=Session(parse_args(['--demo','--db',str(Path(tmp)/'demo.db'),'--disappear-seconds','.2']))
            session.start();server=make_server(session,0)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            base=f'http://127.0.0.1:{server.server_port}'
            def action(name):
                request=Request(base+'/api/simulator',data=json.dumps({'action':name}).encode(),headers={'Content-Type':'application/json','X-DeskMind':'1'})
                with urlopen(request,timeout=5) as r:return json.load(r)
            try:
                deadline=time.monotonic()+3
                while not session.snapshot()['objects'] and time.monotonic()<deadline:time.sleep(.05)
                with urlopen(base+'/') as r:self.assertIn(b'Simulation director',r.read())
                self.assertFalse(action('phone_hide')['phone_present'])
                deadline=time.monotonic()+3
                while not session.runtime.memory.events(kind='disappeared') and time.monotonic()<deadline:time.sleep(.05)
                self.assertIn('not currently detected',session.ask('When was my phone last seen?'))
                self.assertTrue(action('hydration_start')['hydration_enabled'])
                self.assertFalse(action('reset')['hydration_enabled'])
                with self.assertRaises(HTTPError) as e:action('invalid')
                self.assertEqual(e.exception.code,400);e.exception.close()
                session.switch('stop')
                with self.assertRaises(HTTPError) as e:action('phone_hide')
                self.assertEqual(e.exception.code,409);e.exception.close()
            finally:server.shutdown();server.server_close();session.close()
