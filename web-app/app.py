"""Flask web app that shows Rate My Desk scan results."""

import os

from dotenv import load_dotenv
from flask import Flask, render_template
from pymongo import MongoClient
from history import register_history


def create_app(db=None):
    """Create the Flask app, connecting to MongoDB unless a db is given."""
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev")

    if db is None:
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
        db = client[os.getenv("MONGO_DBNAME", "rate_my_desk")]

    @app.route("/")
    def home():
        scans = db.scans.find({"status": "done"}).sort("created_at", -1).limit(10)
        return render_template("index.html", scans=list(scans))

    @app.route("/health")
    def health():
        return {"status": "ok"}

    register_history(app, db)

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
