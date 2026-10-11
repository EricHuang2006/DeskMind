# Validation — October 10, 2026

## Passed

- **14 core tests** on local Python **3.12.10** and **3.14.7**, plus a fifteenth browser-camera integration test on Python 3.12 with OpenCV installed: detection flicker; appearance/absence debounce; grid-boundary jitter; sustained movement and hydration reset; multiple bottles; reappearance; pet ROI; warning deduplication; grounded queries; persistent SQLite reopening; restart gaps; expired reassociation; invalid configuration; backend contract; camera failure; full scripted scenario; live local HTTP endpoints, frame delivery, and query limits.
- **41-second real runtime rehearsal** (scripted input, actual tracker/rules/SQLite worker): 7 appeared, 3 disappeared, 2 moved, 2 interaction, 6 warning, and 1 observation-gap events. Five object tracks were saved. Rehearsal used an 8-second hydration timer and a separate scratch database.
- Local browser server started successfully at `http://127.0.0.1:8765`; state endpoint returned running, simulation-labeled observations.
- Python source compilation and inspection verified Ultralytics imports are confined to `vision.py`.

## Not yet verified

- Actual webcam capture: this environment exposes no `/dev/video*` camera device.
- Actual desk-object accuracy and camera permissions: require the user to start a real camera and present a bottle/phone. Real local YOLO inference has been verified separately as noted below.
- Browser appearance/interactions have not been verified with an automated browser renderer. HTTP serving and query behavior are tested.
- UGen300/HailoRT: no device, HEF, runtime adapter, or performance benchmark is available.

## Before recording

Run webcam mode on the recording laptop, verify the chosen bottle/phone reliably detect, measure FPS, rehearse the short hydration timer and fixed camera angle, and capture actual-camera footage. Finish/export the proposal PDF, publish the GitHub repository, upload the video, and replace final-slide URL placeholders. See `demo-script.md` and `proposal-outline.md`.

## Live camera feature validation

- Browser camera controls added: Start live camera, Stop camera, Use simulation. Updated running instance: `http://127.0.0.1:8766`. The earlier `8765` instance predates source-control endpoints.
- All **15 tests pass** with installed vision dependencies. The camera integration test uses real JPEG encoding/decoding and a controlled detector to verify confirmed state, separate simulation/real databases, pause/resume gaps, source switching, stopped-frame rejection, and cross-origin request rejection.
- Real `YoloBackend` loaded downloaded `yolo11n.pt` and completed CPU inference on a blank image.
- A real JPEG was posted to the running dashboard and processed through local YOLO; the server returned running live-mode status and an annotated JPEG. This is a real inference/transport check on a synthetic image, not proof of camera capture or target-class accuracy.
- Updated dashboard JavaScript syntax verified. Automatic visual/browser-media testing is unavailable; physical camera access requires user permission in the browser.

Tested local environment: Python 3.12.10, Ultralytics 8.4.175, OpenCV 4.14.0.94, CPU PyTorch 2.14.1+cpu, NumPy 2.2.6. Vision dependency versions are pinned in requirements/pyproject for reproducibility.

## Manual simulator validation

All **17 tests pass** after adding manual scene controls. New coverage verifies a scene stays unchanged even after simulated elapsed time; movement and disappearance queries use real tracker/database events; phone return clears its notice; pet appearance triggers the normal ROI rule; the shortened hydration timer fires only after eight seconds and fabricates no interaction; reset retains history and clears active scene conditions. The simulator HTTP endpoint rejects invalid actions and use outside manual mode. The updated instance runs on the existing `http://127.0.0.1:8766` address using `data/manual-demo.db`.
