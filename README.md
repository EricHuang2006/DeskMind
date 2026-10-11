# DeskMind — An AI Workspace That Sees, Remembers, and Helps

A local **laptop/PC prototype** for ASUS UGen AI League 2026 Stage I and a Computer Networks course assignment. It does **not** run on UGen300. The interchangeable vision interface provides a future UGen300/HailoRT deployment path; that adapter is not implemented.

## Quick start: camera-free rehearsal

Python 3.11+; no extra packages are needed for simulation, dashboard, SQLite, or tests.

```sh
python main.py --demo --hydration-seconds 8
```

Open **http://127.0.0.1:8765**. Stop with Ctrl+C. The dashboard prominently marks this mode **SIMULATION**. It is a scripted integration rehearsal, not proof of webcam detection.

Simulation is **manual by default**. Use the **Simulation director** buttons to move/hide/return the bottle, hide/return the phone, and show/hide a cat. The scene holds until you change it. Inventory and events still use normal confirmation and disappearance delays.

Click **Start 8-second hydration timer** when you reach that scene in the narration. It enables the real hydration rule with an eight-second demonstration interval; sustained bottle movement resets the countdown. It does not create an interaction or warning event directly. Reminders are disabled in manual simulation until you start the timer. Live camera keeps its separately configured hydration interval.

**Reset scene** restores the bottle to the left, returns the phone, hides the cat, and disables the demo timer. It **keeps recorded history**. Use a new `--db` filename for a fresh take. Simulation and camera use separate databases by default.

The legacy automatic 40-second scenario remains available for automated rehearsals:

```sh
python main.py --demo --auto-demo --hydration-seconds 8
```

## Built-in camera from the dashboard

With the vision dependencies installed, click **Start live camera** and allow camera access. The browser captures the built-in camera (video only) and posts resized JPEG frames to local YOLO. Annotated frames, inventory, queries, SQLite events, and rules use actual detections. **Stop camera** releases the device; **Use simulation** selects scripted input again. Real-camera history is separate from simulation history.

If the embedded browser cannot request camera permission, open the same local dashboard URL in Chrome or Firefox. Check browser/OS permissions and close other apps using the camera. No camera is activated just by opening the dashboard. Only one camera-sending tab should be active at once. Reloading or closing the tab releases its media stream; missing frame delivery pauses observation rather than inventing disappearances.

```sh
source .venv/bin/activate
python main.py --demo --hydration-seconds 25
# Then click Start live camera in the dashboard.
```

Alternatively, `python main.py --browser-camera` starts the dashboard waiting for browser frames. Direct OpenCV capture via `--camera 0` remains available. The dashboard stays open after detector/camera errors so you can retry or return to simulation.

Browser camera API reference: [MDN getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia).

## Actual webcam setup

Use **Python 3.11 or 3.12** for broad PyTorch/OpenCV wheel compatibility. On Windows, use `py -3.12` and `.venv\Scripts\activate` in place of the first two commands.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py --camera 0 --device cpu --hydration-seconds 30
```

`yolo11n.pt` is the default lightweight COCO-pretrained model. Its weights may download on the first run; download and warm up before recording. After dependencies and weights are available, inference and assistance run locally. Use `--model /path/to/yolo11n.pt` for already downloaded weights. CPU speed depends on the laptop; reduce `--image-size 320` for a faster trial, with possible accuracy loss.

Camera troubleshooting: close other camera apps, grant OS camera permission, and try `--camera 1`. Camera startup/read/inference failures are logged and pause observation; they do not turn unavailable frames into disappearance events. Restart after fixing the camera. The dashboard indicates stale observations. No video frames are saved to disk.

## What works

- Webcam YOLO adapter for bottle, cup, laptop, keyboard, mouse, cell phone, book, cat, and dog when detected by the model.
- Separate track IDs for multiple same-class objects, appearance confirmation, delayed disappearance, and sustained movement detection.
- Normalized bounding boxes, approximate 3 × 3 desk zones, first/last seen, present state, movement-based interaction timestamps.
- SQLite objects and timestamped `appeared`, `disappeared`, `moved`, `interaction`, `warning` history.
- Pet-in-workspace warning, configurable hydration reminder, and last-seen information when a monitored object disappears.
- Deterministic, read-only queries: “Where is my bottle?”, “When was my phone last seen?”, “What disappeared?”, “What changed recently?”
- Browser dashboard with annotated live frames, debounced inventory, recent history, active assistance, and observation health.

**Interaction means sustained observed object movement.** DeskMind does not measure drinking, medication, hand contact, or intent. A disappearance means loss of detection and can be occlusion rather than removal. A fixed camera is assumed.

## Configuration

```sh
python main.py --camera 0 --confidence 0.4 --image-size 640 \
  --hydration-seconds 30 --disappear-seconds 2 --confirm-frames 3 \
  --roi 0.1,0.15,0.95,0.95 --db data/deskmind.db --port 8765 \
  --monitored bottle 'cell phone' book
```

| Option | Default | Meaning |
|---|---|---|
| `--camera` | `0` | OpenCV camera index |
| `--model` | `yolo11n.pt` | Model name or local weight file |
| `--confidence` | `0.35` | Detection confidence threshold |
| `--device` | `cpu` | Ultralytics inference device |
| `--image-size` | `640` | Inference image size |
| `--max-fps` | `8` | Maximum observation loop rate; not a performance guarantee |
| `--confirm-frames` | `3` | Consecutive observations before presence |
| `--disappear-seconds` | `2` | Missing detection delay before absence |
| `--hydration-seconds` | `1800` | Time since presence confirmation / observed movement |
| `--roi` | `0,0,1,1` | Workspace x1,y1,x2,y2 in normalized image coordinates |
| `--monitored` | bottle, cell phone, book | Labels receiving disappearance warnings |
| `--db` | `data/deskmind.db` / `data/demo.db` | Camera / simulation SQLite database |
| `--port` | `8765` | Local browser server port |
| `--no-ui` | off | Run detection and event memory without a server |
| `--duration` | unlimited | Stop after N seconds for rehearsal/testing |
| `--log-level` | `INFO` | Logging verbosity |

Database defaults are relative to `main.py`, independent of your terminal directory. An explicitly provided relative `--db` path is relative to your terminal directory. For a fresh rehearsal, provide a **new** database filename. Existing events remain persisted across runs. On startup, previously present objects require confirmation again and an `observation_gap` event records that offline presence is unknown. No disappearance is invented for offline time. Hydration timing restarts on reconfirmation. Queries show UTC timestamps; the dashboard uses the browser's local time.

The server binds only to `127.0.0.1`. This is a single-user local tool, not an internet-facing service. Read-only endpoints: `/api/state`, `/api/frame`, `/api/query?q=Where%20is%20my%20bottle%3F`.

## Architecture

```text
Webcam → YoloBackend ─┐
Simulation → DemoBackend ─→ Detection → Tracker → SQLite state + events
Future HailoBackend ─┘                     └→ Rules → warnings + event history
                                               ↑
                           Browser UI ← local HTTP ← grounded Assistant
```

`VisionBackend.detect(frame) -> list[Detection]` is the boundary. A `Detection` contains a canonical label, confidence, and normalized xyxy bbox. Tracking, rules, SQLite, assistant, and the browser UI import no Ultralytics APIs. See [architecture](docs/architecture.md) for adapter requirements and limitations.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests use injected detections and a mocked model/camera, plus a real local HTTP server and SQLite. With OpenCV installed, a browser-camera integration test sends actual encoded JPEGs through the queue/decoder, verifies memory isolation, pause/resume, source switching, and request-origin protection. Both the automatic scenario and manual controls are tested through the normal memory/rule path. These tests verify behavior, not real detector accuracy, real camera availability, or Hailo execution. See [validation](docs/validation.md) for the checks actually run on this environment.

## Before the October 14 submission

1. Run real webcam mode on the demo laptop. Fix camera angle/lighting; use one recognizable bottle and phone. Measure actual FPS and detection reliability rather than claiming a benchmark.
2. Rehearse using a 20–30 second hydration timeout and a fresh camera database. Keep production default at 30 minutes.
3. Record approximately three minutes of **actual webcam** demonstration. Clearly identify any simulated fallback. See [demo script](docs/demo-script.md).
4. Finish the English proposal deck with main content no more than 20 pages, export the proposal PDF, and upload the video.
5. Publish the repository to your own GitHub account; put the actual GitHub and video URLs on the **final slide**. The English [proposal outline](docs/proposal-outline.md) includes the required final-slide placeholders.

The submission requirements and deadline above are the project brief provided by the user; check the organizer/course submission portal for final upload details.

Backend API reference: [Ultralytics prediction documentation](https://docs.ultralytics.com/modes/predict/).
