"""Tests for the register and login pages."""

import mongomock
import pytest

from app import create_app
from users import create_user


@pytest.fixture(name="db")
def fixture_db():
    """Provide an in-memory MongoDB database."""
    return mongomock.MongoClient()["auth_test"]


@pytest.fixture(name="app")
def fixture_app(db):
    """Provide the Flask app backed by the in-memory database."""
    return create_app(db)


def test_register_page(client):
    """The register page loads."""
    assert client.get("/register").status_code == 200


def test_register_creates_user_and_logs_in(client, db):
    """Registering saves the user and logs them in."""
    response = client.post("/register", data={"username": "veer", "password": "pw"})
    assert response.status_code == 302
    assert db.users.find_one({"username": "veer"}) is not None
    with client.session_transaction() as sess:
        assert sess["user"] == "veer"


def test_register_duplicate_username(client, db):
    """Registering a taken username shows an error."""
    create_user(db, "veer", "pw")
    response = client.post("/register", data={"username": "veer", "password": "x"})
    assert b"That username is taken." in response.data


def test_register_missing_fields(client):
    """Registering with blank fields shows an error."""
    response = client.post("/register", data={"username": "", "password": ""})
    assert b"Username and password are required." in response.data


def test_login_page(client):
    """The login page loads."""
    assert client.get("/login").status_code == 200


def test_login_success(client, db):
    """Logging in with the right password stores the user in the session."""
    create_user(db, "veer", "pw")
    response = client.post("/login", data={"username": "veer", "password": "pw"})
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess["user"] == "veer"


def test_login_wrong_password(client, db):
    """Logging in with the wrong password shows an error and no session."""
    create_user(db, "veer", "pw")
    response = client.post("/login", data={"username": "veer", "password": "no"})
    assert b"Wrong username or password." in response.data
    with client.session_transaction() as sess:
        assert "user" not in sess
