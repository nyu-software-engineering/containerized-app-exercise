"""Tests for the ASL web app."""

import io

import mongomock
import pytest
import requests
from pymongo.errors import PyMongoError

from app import classify_image, create_app  # pylint: disable=import-error

# pylint: disable=redefined-outer-name,too-few-public-methods


class FakeResponse:
    """Scripted ML HTTP response."""

    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        """Pretend the request succeeded."""

    def json(self):
        """Return the scripted payload."""
        return self.payload


class BrokenCollection:
    """Collection that always fails."""

    def find(self):
        """Fail on read."""
        raise PyMongoError("down")

    def insert_one(self, _document):
        """Fail on write."""
        raise PyMongoError("down")


class BrokenDatabase:
    """Database that returns a broken collection."""

    def __getitem__(self, _name):
        """Return the broken collection."""
        return BrokenCollection()


class BrokenClient:
    """Mongo client that cannot serve requests."""

    def __getitem__(self, _name):
        """Return the broken database."""
        return BrokenDatabase()


@pytest.fixture
def app():
    """App backed by an in-memory database."""
    return create_app({"MONGO_CLIENT": mongomock.MongoClient()})


def test_index_is_empty(client):
    """The upload page loads before any translations exist."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Picture to letter" in response.data
    history = client.get("/history")
    assert b"No translations yet" in history.data


def test_translate_requires_a_file(client):
    """Posting no image is rejected."""
    response = client.post("/translate", data={})
    assert response.status_code == 400
    assert b"Choose an image first." in response.data


def test_translate_rejects_non_images(client):
    """Only image uploads are accepted."""
    payload = {"image": (io.BytesIO(b"hello"), "notes.txt")}
    response = client.post(
        "/translate",
        data=payload,
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert b"JPG" in response.data


def test_translate_rejects_an_empty_image(client):
    """An empty file is rejected."""
    payload = {"image": (io.BytesIO(b""), "sign.jpg")}
    response = client.post(
        "/translate",
        data=payload,
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert b"empty" in response.data


def test_translate_saves_a_letter(client, monkeypatch):
    """A successful recognition shows up on the page and in history."""

    def fake_classify(_image_bytes, _filename):
        return {"letter": "A", "confidence": 0.5, "error": None}

    monkeypatch.setattr("app.classify_image", fake_classify)
    payload = {"image": (io.BytesIO(b"jpeg-bytes"), "folder/sign.JPG")}
    response = client.post(
        "/translate",
        data=payload,
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert b'class="letter">A<' in response.data
    home = client.get("/")
    assert b"50%" in home.data
    history = client.get("/history")
    assert history.status_code == 200
    assert b"sign.JPG" in history.data


def test_classify_image_reads_the_ml_response(monkeypatch):
    """The ML JSON letter and confidence are normalized."""

    def fake_post(*_args, **_kwargs):
        return FakeResponse({"letter": "b", "confidence": "0.5"})

    monkeypatch.setattr("app.requests.post", fake_post)
    result = classify_image(b"img", "b.jpg")
    assert result["letter"] == "B"
    assert result["confidence"] == 0.5
    assert result["error"] is None


def test_classify_image_rejects_a_non_letter(monkeypatch):
    """Digits are not alphabet letters."""

    def fake_post(*_args, **_kwargs):
        return FakeResponse({"letter": "9", "confidence": 1})

    monkeypatch.setattr("app.requests.post", fake_post)
    result = classify_image(b"img", "nine.jpg")
    assert result["letter"] == "?"


def test_classify_image_when_ml_is_down(monkeypatch):
    """A connection error becomes a visible fallback."""

    def fake_post(*_args, **_kwargs):
        raise requests.ConnectionError("down")

    monkeypatch.setattr("app.requests.post", fake_post)
    result = classify_image(b"img", "a.jpg")
    assert result["letter"] == "?"
    assert result["error"] == "Recognizer is not available yet."


def test_classify_image_when_ml_returns_garbage(monkeypatch):
    """Non-numeric confidence is treated as a failure."""

    def fake_post(*_args, **_kwargs):
        return FakeResponse({"letter": "C", "confidence": "high"})

    monkeypatch.setattr("app.requests.post", fake_post)
    result = classify_image(b"img", "c.jpg")
    assert result["error"] == "Recognizer is not available yet."


def test_pages_when_database_is_down(monkeypatch):
    """Database errors are shown instead of crashing."""

    def fake_classify(_image_bytes, _filename):
        return {"letter": "A", "confidence": 0.5, "error": None}

    monkeypatch.setattr("app.classify_image", fake_classify)
    application = create_app({"MONGO_CLIENT": BrokenClient()})
    test_client = application.test_client()
    index = test_client.get("/")
    assert index.status_code == 200
    history = test_client.get("/history")
    assert history.status_code == 500
    payload = {"image": (io.BytesIO(b"jpeg-bytes"), "sign.jpg")}
    saved = test_client.post(
        "/translate",
        data=payload,
        content_type="multipart/form-data",
    )
    assert saved.status_code == 500
    assert b"Could not reach the database." in saved.data


def test_upload_size_limit():
    """Files over the configured limit are rejected."""
    application = create_app(
        {
            "MONGO_CLIENT": mongomock.MongoClient(),
            "MAX_CONTENT_LENGTH": 8,
        }
    )
    test_client = application.test_client()
    payload = {"image": (io.BytesIO(b"0123456789"), "sign.jpg")}
    response = test_client.post(
        "/translate",
        data=payload,
        content_type="multipart/form-data",
    )
    assert response.status_code == 413
    assert b"5 MB" in response.data
    