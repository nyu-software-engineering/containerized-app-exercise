"""Hand pose logic: which fingers are up, which chord that pose is, and the
hold timer + dropout counter that keep the chord steady between frames.

Works on plain lists of 21 (x, y) points, so it doesn't need MediaPipe or a
camera. hands.py is the only file that imports MediaPipe.
"""

import math
from dataclasses import dataclass

# starting values from the plan, tune them on real hands
FINGER_RATIO = 1.1
THUMB_RATIO = 1.2
HOLD_MS = 120
DROPOUT_MS = 300

# fingers are (thumb, index, middle, ring, pinky), 1 = up
# 1-4 count up from the index finger, 5 is all five,
# 6-8 count up again with the thumb out
POSES = {
    1: (0, 1, 0, 0, 0),
    2: (0, 1, 1, 0, 0),
    3: (0, 1, 1, 1, 0),
    4: (0, 1, 1, 1, 1),
    5: (1, 1, 1, 1, 1),
    6: (1, 0, 0, 0, 0),
    7: (1, 1, 0, 0, 0),
    8: (1, 1, 1, 0, 0),
}
FIST = (0, 0, 0, 0, 0)
DEGREE_BY_FINGERS = {fingers: degree for degree, fingers in POSES.items()}

# MediaPipe point numbers
WRIST = 0
THUMB_BASE = 2
THUMB_TIP = 4
PINKY_BASE = 17
FINGER_TIPS = (8, 12, 16, 20)
FINGER_MIDDLE_JOINTS = (6, 10, 14, 18)


def distance(a, b, aspect):
    """Distance between two points. x is scaled by width / height so x and y
    are in the same units."""
    return math.hypot((a[0] - b[0]) * aspect, a[1] - b[1])


def fingers_up(points, aspect, finger_ratio=FINGER_RATIO, thumb_ratio=THUMB_RATIO):
    """Return (thumb, index, middle, ring, pinky) with 1 for each finger that's up.

    A finger is up when its tip is farther from the wrist than its middle joint.
    The thumb is out when its tip is far from the base of the pinky.
    """
    thumb_reach = distance(points[THUMB_TIP], points[PINKY_BASE], aspect)
    thumb_base = distance(points[THUMB_BASE], points[PINKY_BASE], aspect)
    thumb = int(thumb_reach > thumb_ratio * thumb_base)

    others = []
    for tip, joint in zip(FINGER_TIPS, FINGER_MIDDLE_JOINTS):
        tip_dist = distance(points[WRIST], points[tip], aspect)
        joint_dist = distance(points[WRIST], points[joint], aspect)
        others.append(int(tip_dist > finger_ratio * joint_dist))

    return (thumb, *others)


def pose_for_fingers(fingers):
    """Return the scale degree 1-8, "fist", or None if it's not one of our poses."""
    fingers = tuple(fingers)
    if fingers == FIST:
        return "fist"
    return DEGREE_BY_FINGERS.get(fingers)


@dataclass
class PoseTracker:
    """Keeps track of the chord for one session.

    - a new pose only counts after it's held for hold_ms, so the poses you pass
      through while switching don't play
    - a fist, or the hand gone longer than dropout_ms, means silence
    - a pose that isn't in the table keeps the current chord
    - the hand disappearing for dropout_ms or less and coming back is a dropout
    """

    hold_ms: float = HOLD_MS
    dropout_ms: float = DROPOUT_MS
    degree: int | None = None  # the chord that should be playing, None = silence
    stable: bool = False  # True when the current pose matches what's playing
    dropouts: int = 0
    candidate: tuple | None = None  # (pose, time it started)
    gone_since: float | None = None

    def update(self, fingers, now_ms):
        """Feed in one frame. fingers is None when the hand isn't in frame."""
        if fingers is None:
            if self.gone_since is None:
                self.gone_since = now_ms
            if now_ms - self.gone_since > self.dropout_ms:
                self.degree = None
                self.candidate = None
            self.stable = False
            return

        if self.gone_since is not None:
            if now_ms - self.gone_since <= self.dropout_ms:
                self.dropouts += 1
            self.gone_since = None

        pose = pose_for_fingers(fingers)
        if self.candidate is None or self.candidate[0] != pose:
            self.candidate = (pose, now_ms)
        if pose is not None and now_ms - self.candidate[1] >= self.hold_ms:
            self.degree = None if pose == "fist" else pose
        self.stable = pose == ("fist" if self.degree is None else self.degree)
