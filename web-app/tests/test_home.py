"""Tests for the home page."""

import pytest
from app import app, db


@pytest.fixture
def client():
    """Make a test client that is logged in as ben."""
    db.users.delete_many({})
    db.sounds.delete_many({})

    test_client = app.test_client()
    test_client.post(
        "/signup",
        data={"username": "ben", "email": "ben@test.com", "password": "password123"},
    )
    test_client.post("/login", data={"username": "ben", "password": "password123"})
    return test_client


def get_user_id():
    """Get ben's id the same way the app stores it on sounds."""
    return str(db.users.find_one({"username": "ben"})["_id"])


def test_home_needs_login():
    """Logged out users get sent to the login page."""
    response = app.test_client().get("/home")
    assert response.status_code == 302


def test_home_no_sounds(client):  # pylint: disable=redefined-outer-name
    """With no sounds the page shows the empty message."""
    response = client.get("/home")
    assert b"Welcome ben!" in response.data
    assert b"recorded any sounds yet" in response.data


def test_home_shows_my_sounds(client):  # pylint: disable=redefined-outer-name
    """Only the logged in user's sounds show up."""
    db.sounds.insert_one(
        {"user_id": get_user_id(), "name": "Glass tap", "instrument": {"type": "bell"}}
    )
    db.sounds.insert_one({"user_id": "someone else", "name": "Not mine"})

    response = client.get("/home")
    assert b"Glass tap" in response.data
    assert b"bell" in response.data
    assert b"Not mine" not in response.data


def test_home_sound_not_analyzed(client):  # pylint: disable=redefined-outer-name
    """A sound with no instrument yet still shows up."""
    db.sounds.insert_one({"user_id": get_user_id(), "name": "New clip"})

    response = client.get("/home")
    assert b"New clip" in response.data
    assert b"not generated yet" in response.data
