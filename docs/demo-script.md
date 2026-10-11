# DeskMind recording checklist — approximately 2 minutes 50 seconds

Use **30 seconds of slides, 10 seconds of actual detection, a 10-second transition, 90 seconds of controlled simulation, and 30 seconds of slides to finish**. This leaves a little room for natural pauses within an approximately three-minute video. A 60-second simulation is possible, but would give viewers less time to read the answers and warnings.

The recording shows real laptop detection briefly, then explicitly labeled simulation. The simulation uses the actual tracker, SQLite memory, queries, and rules with scripted detection inputs. It does not prove detector accuracy or UGen300 execution.

## Before pressing Record

1. Open the introduction slides and the DeskMind dashboard at `http://127.0.0.1:8766` in separate tabs/windows. Rehearse switching between them.
2. In DeskMind, click **Start live camera** and allow access. Warm up YOLO and confirm one bottle or other reliable supported object detects consistently. Fix the camera angle and lighting. Leave camera mode running, ready for the live segment; do not spend the ten seconds requesting permission or loading the model.
3. Rehearse simulation once: **Use simulation** → **Reset scene** → wait two seconds. Check that the bottle is at **middle-left**, the phone is present, the cat is absent, and the hydration timer is off. Then return to live camera and let detection settle before recording.
4. If clean event history is needed, start a new take with a new simulation database before this rehearsal. Reset scene keeps existing event history. Use a new filename for each recording take; avoid restarting during the recording.
5. Make the controls, inventory, warnings, and query answers readable at the recording resolution. Keep the **SIMULATED** badge visible during that segment.
6. Start the recording on the introduction slide. Use the absolute timestamps below as pacing targets. Wait for the specified result before continuing; a few extra seconds are better than showing an unfinished transition.

## Exact sequence

| Video time | What to click/show | What must be visible | Suggested narration |
|---|---|---|---|
| **0:00–0:30** | Introduction PPT: title, desk problem, and the three functions | DeskMind name and “sees, remembers, helps” | “DeskMind is an AI workspace that sees, remembers, and helps. Object detection alone tells us what is visible now. DeskMind adds temporal memory so we can recall where an object was last observed, understand changes, and receive useful reminders. This is our laptop prototype.” |
| **0:30–0:40** | Switch to the already-running live-camera dashboard. Show the prepared object; make no simulation clicks. | Camera image, real detection box, and confirmed inventory | “Here is actual local YOLO detection from the laptop camera. Vision accuracy still depends on the scene.” |
| **0:40–0:50** | Click **Use simulation**, then **Reset scene**. Wait **two seconds**. | Simulation badge; bottle left, phone present, no cat, timer off | “For the remaining workflow, we use clearly labeled, controlled simulation. The tracker, memory, and assistance rules are the same application logic.” |
| **0:50–1:00** | Click the query chip **Where is my bottle?** | Answer says **middle-left** | “DeskMind answers from stored observations. The bottle is currently in the middle-left desk zone.” |
| **1:00–1:15** | Click **Bottle → right**. Wait **two seconds**, then click **Where is my bottle?** again. | Bottle at right; answer says **middle-right**; moved/interaction events | “When its position changes, DeskMind updates the location and records an event. Sustained movement suggests interaction; it does not prove drinking.” |
| **1:15–1:28** | Click **Hide phone**. Wait **three seconds**, then click **When was my phone last seen?** | Phone absent; disappearance notice; answer with last timestamp and **bottom-right** | “The phone is no longer detected, but its last observed time and location remain available. In a real camera scene, absence can also mean occlusion.” |
| **1:28–1:35** | Click **Return phone**. Wait **two seconds**. | Phone present again; disappearance notice clears | “When it reappears, its presence is confirmed again.” |
| **1:35–1:41** | Click **Start 8-second hydration timer**. At about **1:37**, click **Show cat** and wait **two seconds**. | Timer counting down; cat box; pet warning | “The hydration interval is shortened to eight seconds for this demo. A pet detected in the workspace also produces a warning.” |
| **1:41–1:48** | Click **Hide cat**. Wait **three seconds**. Point to the hydration reminder once it appears, around **1:44**. | Cat warning clears; hydration reminder is visible | “The reminder means no bottle movement was observed during the interval. It does not measure whether I drank.” |
| **1:48–1:55** | Click **Bottle → left**. Wait **two seconds**. | Movement event; hydration reminder clears and countdown restarts | “Observed bottle movement resets the reminder.” |
| **1:55–2:10** | Click **Reset scene** to disable the demonstration timer while retaining history, then click **What changed recently?** Point to its answer and **Recent events**. Expand **Details** on a moved or disappeared event if time permits. | Timestamped changes and their stored details | “Resetting the scene keeps recorded history. These answers are grounded in stored events rather than generated guesses. SQLite preserves the observations across runs.” |
| **2:10–2:20** | Hold on the history answer and inventory; stop pressing controls. | History and latest object state remain readable | “This demonstrates location memory, last-seen recall, and proactive assistance from one observation pipeline.” |
| **2:20–2:40** | Return to PPT: results and architecture slide | Detection → tracking → SQLite → rules/queries; laptop status and future adapter path | “The working prototype combines local detection, temporal memory, persistent history, and deterministic assistance. The vision backend is replaceable. Our next step is validating a Hailo adapter on actual UGen300 hardware; current hardware execution is not claimed.” |
| **2:40–2:50** | Final PPT slide: repository and demo links | GitHub URL, team/project name; video link if already available | “The repository contains the implementation and tests. Thank you.” |

## Small timing details that matter

- **Use the query chips**; typing questions costs time and creates avoidable recording mistakes.
- Presence/movement require confirmation frames. The two-second pauses above include time for the dashboard to refresh. Disappearance needs a longer pause; use three seconds.
- **Do not move the bottle between 1:35 and 1:48.** Movement resets the hydration countdown and would delay the reminder.
- At **1:55**, reset the scene to turn the shortened timer off. The scene is already back at its initial layout, so this keeps the history segment free of another reminder.
- **Reset scene preserves history.** Explicitly show that the earlier events remain available after the reset.
- If the live detector misses during the ten-second segment, hold the prepared object steady and wait briefly. Do not describe simulated boxes as live detection.
- Fill the actual video URL into the **proposal PDF’s final slide after uploading**. If it is not available while recording, the video’s closing slide can show the repository; the required submission slide must ultimately contain both links.

## Slide allocation

Use one or two slides for the opening, one results/architecture slide for the wrap-up, and the required final links slide. The complete English proposal deck can retain its fuller explanation within the main-content limit of 20 pages; the video does not need to narrate every slide.
