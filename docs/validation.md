# Validation

## Automated coverage

The test suite exercises the tracker, SQLite persistence, rules, queries, simulator, and local HTTP API. Tests cover:

- Appearance and disappearance debouncing, detection flicker, movement confirmation, and grid-boundary jitter.
- Multiple objects, approximate reassociation, reappearance, and restart observation gaps.
- Hydration timing, pet ROI warnings, missing-object notices, and warning deduplication.
- Grounded history queries and persistence across database reopening.
- Configuration validation, backend contracts, and camera failures.
- Manual simulation controls and the automatic scenario through the normal memory and rule pipeline.
- HTTP state, frame and query endpoints, source switching, and request-origin protection.

With OpenCV installed, the browser-camera integration test uses encoded JPEG frames and a controlled detector to exercise decoding, memory isolation, paused delivery, and resumed observation. These tests verify application behavior; they do not measure pretrained detector accuracy.

Run the suite from the repository root:

```sh
python -m unittest discover -s tests -v
```

## Prototype verification

Local YOLO inference and browser JPEG transport have been exercised. The laptop prototype has also been demonstrated with actual camera input. Controlled simulation demonstrates temporal memory and assistance using scripted detections, while retaining the real tracker, database, rules, and query implementation.

## Limits

- No standardized accuracy or sustained-performance benchmark is provided. Live detection depends on lighting, camera angle, object size, and the computer.
- Automated camera tests use controlled detections; they do not verify physical camera permissions or recognition quality.
- Browser presentation and media permissions require manual checking on the target computer.
- UGen300/HailoRT execution is not implemented or verified. There is no hardware performance claim.
- Observed object movement is an interaction proxy. Drinking is not measured, and disappearance can result from occlusion.
