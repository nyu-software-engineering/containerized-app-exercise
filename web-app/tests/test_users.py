"""Tests for the user account helpers."""

import mongomock
import pytest

from users import create_user, find_user, verify_user


@pytest.fixture(name="db")
def fixture_db():
    """Provide an in-memory MongoDB database."""
    return mongomock.MongoClient()["users_test"]


def test_create_user_stores_hashed_password(db):
    """New users are saved with a hash, never the plain password."""
    create_user(db, "veer", "secret")
    user = find_user(db, "veer")
    assert user["password_hash"] != "secret"
    assert "password" not in user


def test_create_user_rejects_duplicate(db):
    """A username can only be registered once."""
    create_user(db, "veer", "secret")
    with pytest.raises(ValueError):
        create_user(db, "veer", "other")


def test_create_user_requires_fields(db):
    """Empty usernames or passwords are rejected."""
    with pytest.raises(ValueError):
        create_user(db, "", "secret")
    with pytest.raises(ValueError):
        create_user(db, "veer", "")


def test_find_user_missing(db):
    """Looking up an unknown username returns None."""
    assert find_user(db, "nobody") is None


def test_verify_user_correct_password(db):
    """The right password returns the user."""
    create_user(db, "veer", "secret")
    assert verify_user(db, "veer", "secret")["username"] == "veer"


def test_verify_user_wrong_password(db):
    """A wrong password or an unknown user returns None."""
    create_user(db, "veer", "secret")
    assert verify_user(db, "veer", "wrong") is None
    assert verify_user(db, "nobody", "secret") is None
