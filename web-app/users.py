"""Helpers for storing and checking user accounts in MongoDB."""

from werkzeug.security import check_password_hash, generate_password_hash


def find_user(db, username):
    """Return the user document with this username, or None."""
    return db.users.find_one({"username": username})


def create_user(db, username, password):
    """Create a user with a hashed password and return the new user's id."""
    if not username or not password:
        raise ValueError("Username and password are required.")
    if find_user(db, username):
        raise ValueError("That username is taken.")
    result = db.users.insert_one(
        {"username": username, "password_hash": generate_password_hash(password)}
    )
    return result.inserted_id


def verify_user(db, username, password):
    """Return the user if the username and password match, otherwise None."""
    user = find_user(db, username)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None
