"""Tests for the leaderboard page."""

import mongomock
import pytest

from app import create_app
from leaderboard import top_scans


@pytest.fixture(name="db")
def fixture_db():
    """Provide an in-memory database with a few rated desks."""
    db = mongomock.MongoClient()["leaderboard_test"]
    db.scans.insert_many(
        [
            {"user": "veer", "status": "done", "score": 12, "tier": "Monk"},
            {"user": "yusef", "status": "done", "score": 90, "tier": "Crime Scene"},
            {"user": "denise", "status": "done", "score": 40, "tier": "Lived-in"},
            {"user": "levi", "status": "pending"},
        ]
    )
    return db


def test_top_scans_cleanest_first(db):
    """Cleanest desks come first by default and pending scans are skipped."""
    users = [scan["user"] for scan in top_scans(db)]
    assert users == ["veer", "denise", "yusef"]


def test_top_scans_messiest_first(db):
    """Messiest desks come first when asked."""
    users = [scan["user"] for scan in top_scans(db, messiest=True)]
    assert users == ["yusef", "denise", "veer"]


def test_top_scans_limit(db):
    """Only the requested number of scans is returned."""
    assert len(top_scans(db, limit=2)) == 2


def test_leaderboard_page(db):
    """The leaderboard page shows finished scans."""
    response = create_app(db).test_client().get("/leaderboard")
    assert response.status_code == 200
    assert b"yusef: 90 (Crime Scene)" in response.data
    assert b"levi" not in response.data


def test_leaderboard_page_empty():
    """The leaderboard says so when nothing has been rated."""
    empty_db = mongomock.MongoClient()["leaderboard_empty"]
    response = create_app(empty_db).test_client().get("/leaderboard")
    assert b"No desks rated yet." in response.data
