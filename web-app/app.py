"""Web app for the rock paper scissors game."""

import os

from dotenv import load_dotenv
from flask import Flask
from pymongo import MongoClient

load_dotenv()


def create_app():
    """Create the Flask app and connect it to MongoDB."""
    app = Flask(__name__)

    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    app.db = client[os.getenv("MONGO_DBNAME", "rps")]

    @app.route("/")
    def home():
        """Show how many games are stored, to prove the database works."""
        count = app.db.games.count_documents({})
        return f"Rock Paper Scissors. Games played so far: {count}"

    return app
