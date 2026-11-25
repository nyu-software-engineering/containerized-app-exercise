"""Fake backend so I can look at and design the UI before the real server / client etc is up
Mocks getting hand position data - it just cycles through C major chords every 2 seconds.
To see the UI
Run this from web-app/: `pipenv run python mock_server.py`, then go to
http://localhost:5050
"""

import time

from flask import Flask, jsonify, render_template

app = Flask(__name__)
START_TIME = time.time()

# chord name and notes for degrees 1-8 in C major
FAKE_CHORDS = [
    ("C", ["C4", "E4", "G4"]),
    ("Dm", ["D4", "F4", "A4"]),
    ("Em", ["E4", "G4", "B4"]),
    ("F", ["F4", "A4", "C5"]),
    ("G", ["G4", "B4", "D5"]),
    ("Am", ["A4", "C5", "E5"]),
    ("Bdim", ["B4", "D5", "F5"]),
    ("C", ["C5", "E5", "G5"]),
]


@app.route("/")
def play():
    """Play page."""
    return render_template("play.html")


@app.route("/api/session/start", methods=["POST"])
def start_session():
    """Fake session start."""
    return jsonify(session_id="fake-session")


@app.route("/api/frame", methods=["POST"])
def frame():
    """Ignore the frame and send back the next chord."""
    degree = int(time.time() - START_TIME) // 2 % 8 + 1
    name, notes = FAKE_CHORDS[degree - 1]
    left = {"degree": degree, "chord": name, "notes": notes, "stable": True}
    return jsonify(hand_found=True, fingers=None, left=left, hands=[])


@app.route("/api/session/stop", methods=["POST"])
def stop_session():
    """Fake session stop."""
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(port=5050, debug=True)
