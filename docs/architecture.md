# Architecture and deployment path

## Boundary

The current laptop backend accepts a BGR OpenCV frame. It returns backend-neutral `Detection(label, confidence, bbox)` values with normalized coordinates in the **original input frame**. Required invariants: finite values, confidence in [0,1], positive-size boxes within [0,1], canonical class names. The rest of the app never receives model tensors/results.

A future Hailo adapter must implement the same `detect(frame)` contract. `HailoBackend` currently raises `NotImplementedError` intentionally. We have no UGen300, no HEF artifact, and no hardware benchmark. There is no fallback that falsely labels laptop inference as Hailo.

Hardware deployment tasks:

1. Obtain UGen300 and verify its documented host/runtime/model compatibility.
2. Choose a compatible trained model and perform the required conversion/quantization/compilation into a HEF, with calibration data appropriate to the desk scene.
3. Implement camera preprocessing, color conversion, resize/letterbox, HailoRT inference, class mapping, confidence handling, and required decoding/NMS.
4. Undo preprocessing geometry to produce normalized boxes in the original camera frame.
5. Run the adapter contract tests, then compare accuracy, latency, sustained FPS, memory use, and behavior on actual hardware.
6. Select the Hailo adapter in the runtime only after that validation. Tracking/database/rules/UI remain unchanged.

## Temporal model

A spatial greedy matcher pairs same-class detections with approximate tracks. Candidate appearance needs consecutive hits; an unconfirmed missing candidate is discarded. A confirmed track becomes absent only after a configurable interval without detections. Reappearance needs confirmation too. The association radius is 0.7 in normalized coordinates to support the demo's coarse left-to-right relocation; the tradeoff is weak identity guarantees when several identical objects move. Historical absent tracks are eligible for approximate reassociation for 300 seconds, after which a new ID is assigned. These are local track IDs, not biometric or physical object identity.

Bounding boxes are exponentially smoothed. Sustained raw-center displacement of at least 0.08 image units from the last confirmed movement anchor, staying near a new target for three observations, creates `moved` and `interaction`. Jitter near grid boundaries does not itself imply interaction. Movement inside the same zone can still produce an event. Motion of the camera itself affects all boxes; use a fixed camera.

State and events are written together in SQLite transactions with serialized access. Each successful frame updates last-seen state. A new process inserts an `observation_gap` and marks saved presence unconfirmed until observed again. Offline time is unknown. A camera error stops the worker and makes the UI stale; it does not feed empty detections into the tracker. No persistent frame/video archive is created.

Rules evaluate stable presence; pet warning uses the smoothed bbox center inside the configured ROI (not whole-box overlap). Hydration uses elapsed time since current-session presence confirmation or the most recent sustained movement. Each warning is recorded only when activated; it clears when its condition no longer applies. Missing-object notices last until that track reappears in the current session. Prior disappearance records remain queryable after restart.

## Computer Networks relevance

The browser communicates with a local HTTP server over the loopback TCP interface. JSON state/query responses and JPEG camera frames (SVG only in simulation) cross this boundary. A background worker owns the observation loop; synchronized reads prevent partially updated state from reaching the client. Browser polling limits update frequency; fresh responses disable caching. SQLite is an embedded local persistence layer, not a network database.

This demonstrates a client/server boundary and data exchange. It does not claim distributed deployment or network offloading to UGen300. Future host/device integration must be measured and explained based on real hardware capabilities.

## MVP limitations

- Only pretrained supported classes; keys, AirPods, and USB drives are not essential or advertised.
- A single camera cannot resolve full occlusion or reliably identify identical crossing objects.
- Detector accuracy and FPS depend on lighting, object scale, model, and laptop.
- Slow inference increases appearance and movement debounce latency.
- Interaction is inferred from object motion; no drinking/contact verification.
- Query parsing covers the documented intents and aliases; it is not a general chatbot.
- State/history grow with use; retention/archiving is outside this short-demo MVP.
- Wall-clock timestamps are used for history. Backward clock changes stop observation instead of producing invalid temporal events.

## Browser camera input

A user-triggered `getUserMedia` request captures video without audio. A hidden canvas resizes frames to at most 960 pixels wide, and the browser posts JPEGs over same-origin loopback HTTP. A bounded latest-frame queue feeds the existing YOLO adapter. The worker decodes, detects, tracks, saves events, and returns annotated JPEG frames. Source switching stops the previous worker and uses separate databases for simulated and real observations. If frame delivery pauses for five seconds, presence is stale; resumed delivery reconfirms objects with an observation-gap event instead of inferring changes during downtime. Camera controls require same-origin requests with an explicit request header; the service remains localhost-only.

## Presenter-controlled simulation

`ManualSimulator` implements the same Detection interface and emits stable scripted detections according to explicit scene controls. It does not insert database events. Frame-by-frame tracking produces appearance, disappearance, movement, and inferred-interaction events normally. The hydration button configures an actual eight-second rule interval and sets the start of that countdown; it never fabricates observed interaction. Manual simulation starts with hydration disabled so a reminder cannot interrupt the earlier narration. Reset restores input state and disables the countdown without deleting history. `--auto-demo` retains the separate repeating scenario for smoke tests.
