"""Tests for the Flask web app."""

import mongomock
import pytest

from app import create_app


@pytest.fixture(name="db")
def fixture_db():
    """Provide an in-memory MongoDB database."""
    return mongomock.MongoClient()["test"]


@pytest.fixture(name="app")
def fixture_app(db):
    """Provide the Flask app backed by the in-memory database."""
    return create_app(db)


def test_home_with_no_scans(client):
    """The home page says so when nothing has been rated."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"No desks rated yet." in response.data


def test_home_lists_done_scans(client, db):
    """The home page lists finished scans and skips pending ones."""
    db.scans.insert_many(
        [
            {"user": "veer", "status": "done", "score": 42, "tier": "Lived-in"},
            {"user": "levi", "status": "pending"},
        ]
    )
    response = client.get("/")
    assert b"veer: 42 (Lived-in)" in response.data
    assert b"levi" not in response.data


def test_health(client):
    """The health check reports ok."""
    assert client.get("/health").get_json() == {"status": "ok"}


def test_create_app_without_db():
    """The app builds its own MongoDB client when no db is passed."""
    assert create_app().name == "app"


def test_secret_key_from_env(monkeypatch, db):
    """The secret key comes from the SECRET_KEY environment variable."""
    monkeypatch.setenv("SECRET_KEY", "test-key")
    assert create_app(db).secret_key == "test-key"
