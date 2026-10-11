"""Switch inputs without mixing simulated memory with real camera observations."""
from copy import copy
from pathlib import Path
import threading
from .runtime import Runtime

class Session:
    def __init__(self, args):
        self.args = copy(args)
        self.lock = threading.RLock()
        self.runtime = Runtime(args)

    def start(self):
        self.runtime.start()

    def switch(self, source):
        if source not in ('demo', 'browser', 'webcam', 'stop'):
            raise ValueError('Unknown camera source')
        with self.lock:
            # Stop the old worker before changing its database/source.
            self.runtime.close()
            if self.runtime.thread.is_alive():
                raise RuntimeError('Detector is still loading or busy. Please retry shortly.')
            args = copy(self.args)
            args.demo = source == 'demo'
            args.browser_camera = source in ('browser', 'stop')
            base = Path(self.args.db)
            args.db = base if args.demo == self.args.demo else base.with_name('demo.db' if args.demo else 'deskmind.db')
            self.runtime = Runtime(args)
            if source == 'stop':
                self.runtime.status = 'paused'
                self.runtime.stop.set()
            else:
                self.runtime.start()
            return self.runtime.snapshot()

    def snapshot(self):
        with self.lock:
            return self.runtime.snapshot()

    def frame(self):
        with self.lock:
            return self.runtime.frame()

    def ask(self, question):
        with self.lock:
            return self.runtime.ask(question)

    def submit_frame(self, data):
        with self.lock:
            self.runtime.submit_frame(data)

    def simulator_action(self, name):
        with self.lock:
            return self.runtime.simulator_action(name)

    def close(self):
        with self.lock:
            self.runtime.close()
