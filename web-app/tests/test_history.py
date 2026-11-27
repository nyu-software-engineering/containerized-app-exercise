"""Tests for the history page."""

from datetime import datetime

import mongomock
import pytest

from app import create_app
from history import user_scans


@pytest.fixture(name="db")
def fixture_db():
    """Provide an in-memory database with scans from two users."""
    db = mongomock.MongoClient()["history_test"]
    db.scans.insert_many(
        [
            {
                "user": "veer",
                "status": "done",
                "score": 70,
                "tier": "Chaos",
                "created_at": datetime(2026, 11, 20),
            },
            {
                "user": "veer",
                "status": "done",
                "score": 30,
                "tier": "Tidy",
                "created_at": datetime(2026, 11, 24),
            },
            {"user": "veer", "status": "pending", "created_at": datetime(2026, 11, 25)},
            {
                "user": "yusef",
                "status": "done",
                "score": 90,
                "tier": "Crime Scene",
                "created_at": datetime(2026, 11, 22),
            },
        ]
    )
    return db


def logged_in_client(db, username):
    """Return a test client with the given user already logged in."""
    client = create_app(db).test_client()
    with client.session_transaction() as sess:
        sess["user"] = username
    return client


def test_user_scans_newest_first(db):
    """A user's finished scans come back newest first, without pending ones."""
    assert [scan["score"] for scan in user_scans(db, "veer")] == [30, 70]


def test_user_scans_only_that_user(db):
    """Only the given user's scans are returned."""
    assert [scan["score"] for scan in user_scans(db, "yusef")] == [90]


def test_history_requires_login(db):
    """Logged-out visitors are sent to the login page."""
    response = create_app(db).test_client().get("/history")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_history_shows_own_scans(db):
    """The history page lists the user's scans and not other users'."""
    response = logged_in_client(db, "veer").get("/history")
    assert response.status_code == 200
    assert b"Nov 24, 2026" in response.data
    assert b"Tidy" in response.data
    assert b"Crime Scene" not in response.data


def test_history_empty(db):
    """A user with no scans sees a message."""
    response = logged_in_client(db, "levi").get("/history")
    assert b"No scans yet." in response.data
