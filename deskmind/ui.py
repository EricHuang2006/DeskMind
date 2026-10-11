"""Local camera controls and browser UI served by the Python standard library."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json

HTML = Path(__file__).with_name('dashboard.html')

class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True

def make_server(runtime, port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = urlparse(self.path)
            if route.path == '/':
                self.send(200, HTML.read_bytes(), 'text/html; charset=utf-8')
            elif route.path == '/api/state':
                self.send(200, json.dumps(runtime.snapshot()).encode(), 'application/json')
            elif route.path == '/api/query':
                question = parse_qs(route.query).get('q', [''])[0]
                if len(question) > 500:
                    self.send(400, b'Query too long', 'text/plain'); return
                self.send(200, json.dumps({'answer': runtime.ask(question)}).encode(), 'application/json')
            elif route.path == '/api/frame':
                image, content_type = runtime.frame()
                self.send(200 if image else 503, image or b'Waiting for first frame', content_type if image else 'text/plain')
            else:
                self.send(404, b'Not found', 'text/plain')

        def do_POST(self):
            # Only same-origin dashboard requests may change source or upload frames.
            expected = f'http://127.0.0.1:{self.server.server_port}'
            origin = self.headers.get('Origin')
            if (self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')
                    or self.headers.get('X-DeskMind') != '1'
                    or (origin and origin not in (expected, expected.replace('127.0.0.1', 'localhost')))):
                self.send(403, b'Use the local DeskMind dashboard', 'text/plain')
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 2_000_000:
                    self.send(413, b'Invalid request size', 'text/plain'); return
                self.connection.settimeout(10)
                body = self.rfile.read(length)
                if len(body) != length:
                    raise ValueError('Incomplete request')
                path = urlparse(self.path).path
                if path == '/api/source':
                    if length > 1000:
                        raise ValueError('Source request too long')
                    state = runtime.switch(json.loads(body)['source'])
                    self.send(200, json.dumps(state).encode(), 'application/json')
                elif path == '/api/simulator':
                    if length > 1000:
                        raise ValueError('Simulator request too long')
                    state = runtime.simulator_action(json.loads(body)['action'])
                    self.send(200, json.dumps(state).encode(), 'application/json')
                elif path == '/api/camera/frame':
                    if self.headers.get('Content-Type') != 'image/jpeg' or not body.startswith(b'\xff\xd8'):
                        raise ValueError('Expected a JPEG camera frame')
                    runtime.submit_frame(body)
                    self.send(202, b'{}', 'application/json')
                else:
                    self.send(404, b'Not found', 'text/plain')
            except (ValueError, KeyError, TypeError) as exc:
                self.send(400, json.dumps({'error': str(exc)}).encode(), 'application/json')
            except RuntimeError as exc:
                self.send(409, json.dumps({'error': str(exc)}).encode(), 'application/json')
            except (OSError, TimeoutError) as exc:
                self.send(503, json.dumps({'error': str(exc)}).encode(), 'application/json')

        def send(self, code, body, content_type):
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Permissions-Policy', 'camera=(self), microphone=()')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    return DashboardServer(('127.0.0.1', port), Handler)
