"""Turn MediaPipe gesture results into a rock, paper or scissors move."""

import math

# MediaPipe's built-in gesture names and the move each one stands for
GESTURE_TO_MOVE = {
    "Closed_Fist": "rock",
    "Open_Palm": "paper",
    "Victory": "scissors",
}
