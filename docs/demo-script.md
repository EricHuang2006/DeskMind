# Demo walkthrough

DeskMind supports actual local YOLO detection and a controllable simulation. Keep the source badge visible so viewers can distinguish camera observations from simulated detections. Both modes use the same tracking, SQLite memory, rules, and query pipeline.

## Live detection

Install the vision dependencies as described in the README, start the dashboard, and click **Start live camera**. Allow camera access and wait for the model to load. Use a fixed camera, good lighting, and clearly visible supported objects such as a laptop, bottle, or phone. Confirm detection boxes and stable inventory before demonstrating the scene.

## Controlled simulation

Start with `python main.py --demo`, or click **Use simulation** in the running dashboard. Click **Reset scene**, then allow about two seconds for presence confirmation.

| Action | Expected result |
|---|---|
| Ask **Where is my bottle?** | The bottle is in the middle-left zone. |
| Click **Bottle → right**, wait two seconds, and ask again. | The location updates to middle-right; movement and interaction events appear. |
| Click **Hide phone**, wait three seconds, then ask **When was my phone last seen?** | The phone is absent; its last observed time and bottom-right location remain available. |
| Click **Return phone** and wait two seconds. | Presence is confirmed and the missing-phone notice clears. |
| Click **Start 8-second hydration timer** and leave the bottle still. | The hydration reminder appears after the shortened demonstration interval. |
| Click **Hide bottle**, wait three seconds, then **Return bottle** and wait two seconds. | The absent bottle stops receiving hydration reminders; reconfirmed presence starts a new interval. This is a reminder-reset proxy, not proof of drinking. |
| Click **Show cat** and wait two seconds. | The pet-in-workspace warning appears. |
| Click **Hide cat** and wait three seconds. | The pet warning clears. |
| Click **Reset scene**, then ask **What changed recently?** | The timer stops and the initial layout returns; earlier events remain queryable. |

The scene holds until a control changes it. Queries use stored observations. Simulation controls change detection inputs rather than directly inserting history events.

## Fresh sessions

**Reset scene retains history.** To start with an empty simulation history, choose an unused database filename:

```sh
python main.py --demo --db data/new-session.db
```

Camera and simulation histories are stored separately. Temporal confirmation introduces short delays, and an object missing from a real camera view may be occluded rather than removed.
