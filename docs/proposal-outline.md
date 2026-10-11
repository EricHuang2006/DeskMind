# English proposal outline — DeskMind

Suggested **12 slides** (main content under the user's 20-page limit). This is an outline, not a finished slide deck or proposal PDF. Replace placeholders with real project/team information and verified measurements.

1. **DeskMind: An AI Workspace That Sees, Remembers, and Helps** — Team/course information. Subtitle: Laptop prototype with a UGen300-targeted deployment path.
2. **Problem** — Objects disappear from the user's attention; frame-only detection cannot answer when/where something was last observed.
3. **User scenario** — Find a bottle or phone, recall recent desk changes, receive a hydration reminder and pet-in-workspace warning.
4. **Solution** — See (local object detection), remember (temporal state and SQLite events), help (grounded queries and rules).
5. **MVP scope** — Webcam; pretrained supported classes; approximate zones; appearance/disappearance/movement; deterministic queries; browser dashboard.
6. **Architecture** — Backend-neutral Detection → temporal tracker → SQLite → supervisor/assistant → local browser UI.
7. **Temporal memory** — Explain appearance confirmation, absence delay, movement debounce, first/last seen, and offline observation gaps with a real recorded example.
8. **Proactive assistance** — Pet ROI, configurable hydration timeout, missing-object last-seen. Observed movement does not prove drinking.
9. **Working laptop demo & validation** — Screenshots from actual camera operation. Insert measured FPS, example detection reliability, test evidence, and limitations. Clearly identify any simulated demonstration.
10. **UGen300 deployment path** — No current UGen300 execution. Future steps: hardware access, compatible model/HEF, HailoRT adapter, original-frame coordinate mapping, measured accuracy/latency/FPS.
11. **Course relevance and next milestones** — Local browser/HTTP/TCP interface, structured JSON exchange, camera frame delivery, persistence. Finish real-camera rehearsal and recording by October 14, 2026. Avoid unmeasured hardware claims.
12. **Repository & Demo Video** — Final slide must include **GitHub: [replace with actual repository URL]** and **Demo video: [replace with actual uploaded video URL]**, plus team contact if desired. Export the finished deck to the proposal PDF used for both submissions.
