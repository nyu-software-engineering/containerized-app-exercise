"""Shared test setup for the web app."""

import mongomock
import pytest

from app import create_app


@pytest.fixture
def app():
    """Create the Flask app with a fake in-memory database."""
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    flask_app.db = mongomock.MongoClient().rps
    return flask_app
