"""Tests for the web app routes."""

import io
from datetime import datetime, timezone
from unittest.mock import Mock

import requests
from pymongo.errors import PyMongoError


def fake_agent(monkeypatch, result):
    """Make the gesture agent reply with the given result, without a real request."""
    response = Mock()
    response.json.return_value = result
    monkeypatch.setattr("app.requests.post", Mock(return_value=response))


def fake_opponent(monkeypatch, move):
    """Make the opponent always play the given move instead of a random one."""
    monkeypatch.setattr("app.random.choice", lambda moves: move)


def send_photo(client, content_type="image/jpeg", data=b"fake image bytes"):
    """Post a fake photo to the play route the same way the browser does."""
    return client.post(
        "/api/plays",
        data={"image": (io.BytesIO(data), "hand.jpg", content_type)},
        content_type="multipart/form-data",
    )


def test_home_page(client):
    """The home page loads and shows the game title."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Rock Paper Scissors" in response.data
    assert b"View history" in response.data


def test_play_win(client, app, monkeypatch):
    """Rock beats scissors, and the round is saved."""
    fake_agent(monkeypatch, {"move": "rock", "confidence": 0.9})
    fake_opponent(monkeypatch, "scissors")

    response = send_photo(client)

    assert response.status_code == 200
    assert response.get_json() == {
        "player_move": "rock",
        "opponent_move": "scissors",
        "outcome": "win",
        "confidence": 0.9,
    }
    saved = app.db.games.find_one()
    assert saved["outcome"] == "win"
    assert saved["image_size"] == len(b"fake image bytes")


def test_play_loss(client, monkeypatch):
    """Rock loses to paper."""
    fake_agent(monkeypatch, {"move": "rock"})
    fake_opponent(monkeypatch, "paper")

    response = send_photo(client)

    assert response.status_code == 200
    assert response.get_json()["outcome"] == "loss"
    assert response.get_json()["confidence"] is None


def test_play_tie(client, monkeypatch):
    """The same move on both sides is a tie."""
    fake_agent(monkeypatch, {"move": "paper"})
    fake_opponent(monkeypatch, "paper")

    response = send_photo(client)

    assert response.status_code == 200
    assert response.get_json()["outcome"] == "tie"
    assert response.get_json()["player_move"] == "paper"


def test_play_without_image(client, app):
    """A request with no photo is rejected and nothing is saved."""
    response = client.post("/api/plays")
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert app.db.games.count_documents({}) == 0


def test_play_wrong_file_type(client):
    """A file that is not an image is rejected."""
    response = send_photo(client, content_type="text/plain")
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert "JPEG" in response.get_json()["error"]


def test_play_empty_image(client):
    """An empty photo is rejected."""
    response = send_photo(client, data=b"")
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert "non-empty" in response.get_json()["error"]


def test_play_agent_down(client, app, monkeypatch):
    """If the agent cannot be reached, the route answers 502 and saves nothing."""
    monkeypatch.setattr("app.requests.post", Mock(side_effect=requests.ConnectionError))

    response = send_photo(client)

    assert response.status_code == 502
    assert "error" in response.get_json()
    assert app.db.games.count_documents({}) == 0


def test_play_unknown_move(client, app, monkeypatch):
    """A move that is not rock, paper or scissors is rejected."""
    fake_agent(monkeypatch, {"move": "lizard"})

    response = send_photo(client)

    assert response.status_code == 502
    assert "unknown hand gesture" in response.get_json()["error"]
    assert app.db.games.count_documents({}) == 0


def test_play_agent_reply_not_a_dictionary(client, monkeypatch):
    """A reply from the agent in the wrong shape is rejected."""
    fake_agent(monkeypatch, ["rock"])

    response = send_photo(client)

    assert response.status_code == 502
    assert "error" in response.get_json()
    assert "unknown hand gesture" in response.get_json()["error"]


def test_play_database_error(client, app, monkeypatch):
    """If the round cannot be saved, the route answers 503."""
    fake_agent(monkeypatch, {"move": "rock"})
    monkeypatch.setattr(app.db.games, "insert_one", Mock(side_effect=PyMongoError))

    response = send_photo(client)

    assert response.status_code == 503
    assert "error" in response.get_json()
    assert "save" in response.get_json()["error"]


def test_play_image_too_large(client, app):
    """A photo over the size limit gets a readable 413 error."""
    app.config["MAX_CONTENT_LENGTH"] = 10

    response = send_photo(client, data=b"more than ten bytes")

    assert response.status_code == 413
    assert "error" in response.get_json()
    assert "8 MB" in response.get_json()["error"]


def test_history_empty(client):
    """With no rounds saved, the history page says so."""
    response = client.get("/history")
    assert response.status_code == 200
    assert b"No rounds played yet." in response.data
    assert b"Wins: 0" in response.data


def test_history_with_rounds(client, app):
    """The history page counts the outcomes and lists the newest round first."""
    app.db.games.insert_many(
        [
            {
                "player_move": "rock",
                "opponent_move": "scissors",
                "outcome": "win",
                "created_at": datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
            },
            {
                "player_move": "paper",
                "opponent_move": "scissors",
                "outcome": "loss",
                "created_at": datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc),
            },
            {
                "player_move": "rock",
                "opponent_move": "rock",
                "outcome": "tie",
                "created_at": datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc),
            },
        ]
    )

    page = client.get("/history").data.decode()

    assert "Wins: 1" in page
    assert "Losses: 1" in page
    assert "Ties: 1" in page
    assert page.index("2026-11-03") < page.index("2026-11-01")
