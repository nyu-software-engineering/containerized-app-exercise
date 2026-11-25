"""Turn MediaPipe gesture results into a rock, paper or scissors move."""

import math

# MediaPipe's built-in gesture names and the move each one stands for
GESTURE_TO_MOVE = {
    "Closed_Fist": "rock",
    "Open_Palm": "paper",
    "Victory": "scissors",
}

WRIST = 0
# (middle joint, fingertip) landmark indexes for index, middle, ring and pinky
FINGERS = {"index": (6, 8), "middle": (10, 12), "ring": (14, 16), "pinky": (18, 20)}


def move_from_gesture(gesture_name):
    """Map a MediaPipe gesture name to a move, or None if it is not one of ours."""
    return GESTURE_TO_MOVE.get(gesture_name)


def _distance(a, b):
    """Distance between two landmarks in the image plane."""
    return math.hypot(a.x - b.x, a.y - b.y)


def extended_fingers(landmarks):
    """A finger is extended when its tip is farther from the wrist than its middle joint."""
    wrist = landmarks[WRIST]
    return {
        name: _distance(landmarks[tip], wrist) > _distance(landmarks[joint], wrist)
        for name, (joint, tip) in FINGERS.items()
    }


def move_from_landmarks(landmarks):
    """Backup rule from the 21 hand landmarks, used when the gesture model is unsure."""
    fingers = extended_fingers(landmarks)
    count = sum(fingers.values())
    if count == 0:
        return "rock"
    if count == 4 or count == 5:
        return "paper"
    if fingers["index"] and fingers["middle"] and count == 2:
        return "scissors"
    return None
