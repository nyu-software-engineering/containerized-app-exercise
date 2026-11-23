gesture piano
left hand holds chords, right hand plays melody

ML client container runs MediaPipe hand tracking on each frame
left hand -- chord combinations choose which chord. for simplicity we just do C major
FIST = nothing playing
Chords: (1 to 8)
1: thumb out
2: thumb index
etc 1 to 5, each time add the next finger
6 to 8 -- subtract a finger starting from the thumb
eg: 6: all fingers except thumb
(this way there are no repeating combos)
(a pose has to be held ~100-150ms before the chord changes, so the in between poses while switching dont trigger)


RH can be melody
vertical scale
pinch to play, if not pinched then notes aren't played but it automatically holds (this way it doesnt slide / play all the notes as it slides up the scale)
FIST = nothing playing

FIST OR HANDS LEAVE SCREEN = MUSIC STOPS PLAYING
(hand has to be gone for ~300ms, so quick tracking glitches dont cut the music)

Architecture:

**Browser: Camera (getUserMedia)**
- Overlay (LH show the finger combos and what chord it is, RH show the vertical -- aka Pose Legend)
- Piano sound (Tone.js)

**Web App (Flask)**
- Port 5000 
- serves play page + dashboard
- forwards frames to ML client
- reads history for dashboard

**ml-client**
- MediaPipe hand tracking
- Pose to chord (LH), pinch to note (RH)
- internal api: POST /analyze
- writes sessions and events

**mongodb**
- official mongo image sessions, events
- history only

main loop, ~ 15–20 times per sec or so:
1.  The browser grabs a camera frame and sends it to Flask.
2.  Flask forwards it to the ML client at http://ml-client:5001/analyze; Compose finds containers by service name.
3.  The ML client runs MediaPipe, works out the left-hand chord and the right-hand pinch, lane and fist, and returns JSON.
4.  The browser draws the overlay and plays the piano.
5.  When a chord or note changes (or the music stops), the ML client saves an event to Mongo.

example response from /analyze:
{
  "left":  {"degree": 3, "chord": "Em", "stable": true},
  "right": {"pinch": true, "lane": 5, "note": "G4", "fist": false}
}
(note: obviously degree has internal mapping from finger combo to degree)
(note on UI: show what the model detects by like showing the note/chord that's being played at the top of the half. like left half top for left hand or something. idk some kind of UI that shows what is being played)
MONGODB:
sessions
- One play session (from start to stop):
- _id, started_at, ended_at, key, scale, dropouts (times tracking dropped out)
events
- One chord change, note played, or stop (only saved when something changes, not every frame)
- session_id, t, hand, type, degree, name
- type = chord / stop for LH, note_on / note_off for RH

example
(t = time, in UTC / Z / Zulu)
{
  "session_id": "6561f0...",
  "t": "2026-11-23T15:33:05.120Z",
  "hand": "left",
  "type": "chord",
  "degree": 4,
  "name": "F"
}
**What the Dashboard Shows**:
Sessions list: date, length, key
Session page: chord timeline, replay with a speed control, and the number of times tracking dropped out
Overall stats: average session length, longest session, favorite chords (a bar chart)

(+ a seed script w some sample sessions so the dashboard isnt empty on first run? optionally- just for demo)


Proj 4 reqs:<br>
**ML client collects sensor data:** <br>
Webcam frames, captured in the browser and passed to the ML client<br>
**ML client does real analysis**<br>
MediaPipe hand landmarks
our pose -> chord and pinch -> note system<br>
**Results saved to MongoDB**<br>
sessions and events collections<br>
**ML client has no UI**<br>
It only exposes an internal API; users only see the web app<br>
**Web app shows activity and results**<br>
Play page (live overlay) + dashboard (session history)<br>
**Flask + pymongo**<br>
Web app<br>
**Three containers, started with Docker Compose**<br>
web-app, ml-client, mongodb (official mongo image)<br>
**black + pylint**<br>
lint workflow already in the repo, runs on every PR<br>
**pytest, 80%+ coverage for both ML client and web app**<br>
test the pose logic w fake hand points, mock MediaPipe + Mongo<br>
**CI for each subsystem**<br>
GitHub Actions builds + tests on merge to main, badge for each in README<br>
**README**<br>
description, teammate links, setup that works on any platform, env.example<br>