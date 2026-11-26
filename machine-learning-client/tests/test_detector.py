"""Tests for detector.py. The YOLO model is mocked so tests run fast without torch."""

import io
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PIL import Image

import detector

NAMES = {0: "cup", 1: "book", 2: "laptop"}


def make_image_bytes():
    """Return the bytes of a small blank PNG."""
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def make_model(detections):
    """Build a fake model that returns the given (class_id, confidence) pairs."""
    boxes = [SimpleNamespace(cls=cls, conf=conf) for cls, conf in detections]
    result = SimpleNamespace(names=NAMES, boxes=boxes)
    return MagicMock(return_value=[result])


def test_counts_each_object_type():
    """Objects of the same type are added up."""
    model = make_model([(0, 0.9), (0, 0.8), (1, 0.7), (0, 0.6), (2, 0.95)])
    counts = detector.detect_objects(make_image_bytes(), model=model, threshold=0.5)
    assert counts == {"cup": 3, "book": 1, "laptop": 1}


def test_ignores_low_confidence_detections():
    """Detections under the threshold are not counted."""
    model = make_model([(0, 0.9), (1, 0.3), (2, 0.49)])
    counts = detector.detect_objects(make_image_bytes(), model=model, threshold=0.5)
    assert counts == {"cup": 1}


def test_detection_exactly_at_threshold_is_counted():
    """A confidence equal to the threshold still counts."""
    model = make_model([(1, 0.5)])
    counts = detector.detect_objects(make_image_bytes(), model=model, threshold=0.5)
    assert counts == {"book": 1}


def test_no_objects_returns_empty_dict():
    """An image with nothing detected gives an empty result."""
    model = make_model([])
    counts = detector.detect_objects(make_image_bytes(), model=model)
    assert isinstance(counts, dict)
    assert not counts


def test_model_gets_image_and_threshold():
    """The model is called with a PIL image and the confidence threshold."""
    model = make_model([])
    detector.detect_objects(make_image_bytes(), model=model, threshold=0.25)
    args, kwargs = model.call_args
    assert isinstance(args[0], Image.Image)
    assert kwargs["conf"] == 0.25


def test_uses_default_model_when_none_given():
    """Without a model argument, the shared model from get_model is used."""
    model = make_model([(2, 0.9)])
    with patch.object(detector, "get_model", return_value=model):
        assert detector.detect_objects(make_image_bytes()) == {"laptop": 1}
    model.assert_called_once()


def test_get_model_loads_weights_once():
    """get_model loads the weights file once and caches the model."""
    fake_yolo = MagicMock()
    fake_ultralytics = SimpleNamespace(YOLO=fake_yolo)
    detector.get_model.cache_clear()
    with patch.dict(sys.modules, {"ultralytics": fake_ultralytics}):
        first = detector.get_model()
        second = detector.get_model()
    detector.get_model.cache_clear()
    fake_yolo.assert_called_once_with(detector.MODEL_PATH)
    assert first is second
