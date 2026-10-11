"""Presenter-controlled detections. Actions change inputs, never inject events."""
import threading
from .vision import Detection

ACTIONS = frozenset({'bottle_left', 'bottle_right', 'bottle_hide', 'bottle_show',
                     'phone_hide', 'phone_show', 'pet_show', 'pet_hide',
                     'hydration_start', 'reset'})

class ManualSimulator:
    def __init__(self):
        self.lock = threading.RLock()
        self.reset()

    def reset(self):
        with self.lock:
            self.bottle_side = 'left'
            self.bottle_present = True
            self.phone_present = True
            self.pet_present = False

    def action(self, name):
        if name not in ACTIONS:
            raise ValueError('Unknown simulator action')
        with self.lock:
            if name == 'reset':
                self.reset()
            elif name in ('bottle_left', 'bottle_right'):
                self.bottle_side = name.split('_')[1]
                self.bottle_present = True
            elif name in ('bottle_hide', 'bottle_show'):
                self.bottle_present = name == 'bottle_show'
            elif name in ('phone_hide', 'phone_show'):
                self.phone_present = name == 'phone_show'
            elif name in ('pet_hide', 'pet_show'):
                self.pet_present = name == 'pet_show'

    def snapshot(self):
        with self.lock:
            return dict(bottle_side=self.bottle_side, bottle_present=self.bottle_present,
                        phone_present=self.phone_present, pet_present=self.pet_present)

    def detect(self, frame):
        with self.lock:
            items = [Detection('laptop', .96, (.35, .12, .67, .42)),
                     Detection('keyboard', .94, (.32, .49, .68, .61))]
            if self.bottle_present:
                x = .12 if self.bottle_side == 'left' else .72
                items.append(Detection('bottle', .92, (x, .38, x + .08, .65)))
            if self.phone_present:
                items.append(Detection('cell phone', .90, (.77, .72, .88, .86)))
            if self.pet_present:
                items.append(Detection('cat', .91, (.42, .65, .61, .92)))
            return items
