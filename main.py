#!/usr/bin/env python3
"""Run the laptop prototype or an explicitly simulated camera-free demonstration."""
import argparse
import logging
import math
from pathlib import Path
import threading
import time
from deskmind.runtime import Runtime
from deskmind.session import Session
from deskmind.ui import make_server
from deskmind.vision import CLASSES

ROOT = Path(__file__).resolve().parent

def roi(value):
    try:
        values = tuple(float(v) for v in value.split(','))
        if len(values) != 4:
            raise ValueError
        x1,y1,x2,y2 = values
        if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
            raise ValueError
        return values
    except ValueError:
        raise argparse.ArgumentTypeError('ROI must be normalized x1,y1,x2,y2 with positive width and height')

def positive(value):
    v = float(value)
    if not math.isfinite(v) or v <= 0:
        raise argparse.ArgumentTypeError('Must be finite and positive')
    return v

def positive_int(value):
    v = int(value)
    if v <= 0:
        raise argparse.ArgumentTypeError('Must be positive')
    return v

def parse_args(argv=None):
    p = argparse.ArgumentParser(description='DeskMind laptop prototype — local detection and temporal memory')
    p.add_argument('--demo', action='store_true', help='Scripted detections; no webcam or vision packages needed')
    p.add_argument('--auto-demo', action='store_true', help='Use the legacy automatic 40-second simulation loop with --demo')
    p.add_argument('--browser-camera', action='store_true', help='Receive camera frames from the browser instead of opening an OpenCV device')
    p.add_argument('--camera', type=int, default=0)
    p.add_argument('--model', default='yolo11n.pt', help='Local weights path or Ultralytics model name (first run may download)')
    p.add_argument('--confidence', type=float, default=.35)
    p.add_argument('--device', default='cpu')
    p.add_argument('--image-size', type=positive_int, default=640)
    p.add_argument('--hydration-seconds', type=positive, default=1800)
    p.add_argument('--disappear-seconds', type=positive, default=2)
    p.add_argument('--confirm-frames', type=positive_int, default=3)
    p.add_argument('--max-fps', type=positive, default=8)
    p.add_argument('--roi', type=roi, default=(0,0,1,1))
    p.add_argument('--monitored', nargs='+', choices=sorted(CLASSES), default=['bottle','cell phone','book'])
    p.add_argument('--db', type=Path, help='Default: data/demo.db in simulation, data/deskmind.db for webcam')
    p.add_argument('--port', type=int, default=8765)
    p.add_argument('--no-ui', action='store_true')
    p.add_argument('--duration', type=positive, help='Exit after this many seconds, for rehearsal/smoke testing')
    p.add_argument('--log-level', choices=['DEBUG','INFO','WARNING','ERROR'], default='INFO')
    args = p.parse_args(argv)
    if args.auto_demo and not args.demo:
        p.error('--auto-demo requires --demo')
    if args.no_ui and args.browser_camera:
        p.error('--browser-camera needs the dashboard; omit --no-ui')
    if args.demo and args.browser_camera:
        p.error('--demo and --browser-camera are mutually exclusive')
    if not (0 < args.confidence <= 1):
        p.error('--confidence must be in (0, 1]')
    if not (1 <= args.port <= 65535):
        p.error('--port must be in 1..65535')
    if args.db is None:
        args.db = ROOT / 'data' / ('demo.db' if args.demo else 'deskmind.db')
    return args

def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format='%(asctime)s %(levelname)s %(message)s')
    runtime = Runtime(args) if args.no_ui else Session(args)
    server = None
    try:
        if not args.no_ui:
            server = make_server(runtime, args.port)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            logging.info('Open http://127.0.0.1:%s — %s', args.port, 'SIMULATION' if args.demo else 'laptop webcam')
        runtime.start()
        started = time.monotonic()
        while not args.no_ui or runtime.thread.is_alive():
            if args.duration and time.monotonic() - started >= args.duration:
                break
            time.sleep(.2)
        return 1 if runtime.snapshot()['status'] == 'error' else 0
    except KeyboardInterrupt:
        return 0
    except OSError as exc:
        logging.error('Cannot start dashboard: %s. Try a different --port.', exc)
        return 1
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        runtime.close()

if __name__ == '__main__':
    raise SystemExit(main())
