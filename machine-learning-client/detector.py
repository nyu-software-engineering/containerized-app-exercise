"""Object detection for Rate My Desk using a pretrained YOLO model."""

import io
import os
from collections import Counter
from functools import lru_cache

from PIL import Image

MODEL_PATH = os.getenv("MODEL_PATH", "yolov8s.pt")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.4"))


@lru_cache(maxsize=1)
def get_model():
    """Load the YOLO model once and reuse it for every scan."""
    # imported here so the worker and tests don't load torch until needed
    from ultralytics import YOLO  # pylint: disable=import-outside-toplevel

    return YOLO(MODEL_PATH)


def detect_objects(image_bytes, model=None, threshold=CONFIDENCE_THRESHOLD):
    """Run detection on an image and return a count of each object type.

    Example return value: {"cup": 3, "book": 5}
    """
    if model is None:
        model = get_model()

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    results = model(image, conf=threshold, verbose=False)

    counts = Counter()
    for result in results:
        for box in result.boxes:
            if float(box.conf) >= threshold:
                counts[result.names[int(box.cls)]] += 1
    return dict(counts)
