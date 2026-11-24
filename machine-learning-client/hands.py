"""MediaPipe wrapper. This is the only file that imports MediaPipe.

Not done yet: use the Tasks HandLandmarker in IMAGE mode with num_hands=2.
The .task model file gets downloaded in the Dockerfile, don't commit it.
"""


def find_hands(jpeg):  # pylint: disable=unused-argument
    """Find the hands in one JPEG frame (bytes).

    Should return (hands, aspect):
    - hands: [{"label": "Left", "points": [(x, y), ...]}, ...] with the 21
      points normalized to 0-1 and not mirrored. "Left" is the player's own
      left hand, since the browser sends unmirrored frames.
    - aspect: the frame's width / height, for logic.fingers_up
    """
    raise NotImplementedError("MediaPipe isn't hooked up yet")
