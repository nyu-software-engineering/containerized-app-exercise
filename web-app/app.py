"""Web app for the camera-based rock paper scissors game."""

import os
import random
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MOVES = ("rock", "paper", "scissors")
WINNING_PAIRS = {
    ("rock", "scissors"),
    ("paper", "rock"),
    ("scissors", "paper"),
}
MAX_IMAGE_SIZE = 8 * 1024 * 1024


def create_app():
    """Create the Flask app and connect it to MongoDB and the gesture agent."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_IMAGE_SIZE

    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    app.db = client[os.getenv("MONGO_DBNAME", "rps")]

    agent_url = os.getenv(
        "ML_CLIENT_URL",
        "http://machine-learning-client:8000/predict",
    )

    @app.route("/")
    def home():
        """Show the game page."""
        games_played = app.db.games.count_documents({})
        return render_template("index.html", games_played=games_played)

    @app.post("/api/plays")
    def play():
        """Send a photo to the agent and save the round result."""
        image = request.files.get("image")
        content_type = image.mimetype if image is not None else ""
        image_bytes = image.read() if image is not None else b""

        if (
            image is None
            or not image.filename
            or content_type not in ALLOWED_IMAGE_TYPES
            or not image_bytes
        ):
            return jsonify(error="Provide a non-empty JPEG, PNG, or WebP image."), 400

        try:
            response = requests.post(
                agent_url,
                files={
                    "image": (
                        image.filename,
                        image_bytes,
                        content_type,
                    )
                },
                timeout=20,
            )
            response.raise_for_status()
            agent_result = response.json()
        except (requests.RequestException, ValueError):
            app.logger.exception("Gesture agent request failed")
            return jsonify(error="The gesture agent could not read that photo."), 502

        player_move = (
            agent_result.get("move") if isinstance(agent_result, dict) else None
        )
        if player_move not in MOVES:
            return jsonify(error="The agent returned an unknown hand gesture."), 502

        opponent_move = random.choice(MOVES)
        if player_move == opponent_move:
            outcome = "tie"
        elif (player_move, opponent_move) in WINNING_PAIRS:
            outcome = "win"
        else:
            outcome = "loss"

        game = {
            "player_move": player_move,
            "opponent_move": opponent_move,
            "outcome": outcome,
            "confidence": agent_result.get("confidence"),
            "image_content_type": content_type,
            "image_size": len(image_bytes),
            "created_at": datetime.now(timezone.utc),
        }

        try:
            app.db.games.insert_one(game)
        except PyMongoError:
            app.logger.exception("Could not save game result")
            return jsonify(error="Could not save the round result."), 503

        return (
            jsonify(
                player_move=player_move,
                opponent_move=opponent_move,
                outcome=outcome,
                confidence=game["confidence"],
            ),
            200,
        )

    @app.route("/history")
    def history():
        """Show past rounds and the win, loss and tie counts."""
        games = list(app.db.games.find().sort("created_at", -1).limit(50))
        stats = {
            "win": app.db.games.count_documents({"outcome": "win"}),
            "loss": app.db.games.count_documents({"outcome": "loss"}),
            "tie": app.db.games.count_documents({"outcome": "tie"}),
        }
        return render_template("history.html", games=games, stats=stats)

    @app.errorhandler(413)
    def image_too_large(_error):
        """Return a readable error for oversized photo uploads."""
        return jsonify(error="Keep the photo under 8 MB."), 413

    return app
