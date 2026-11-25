"""Leaderboard of the cleanest and messiest rated desks."""

from flask import render_template


def top_scans(db, messiest=False, limit=10):
    """Return finished scans by score, cleanest first unless messiest is set."""
    order = -1 if messiest else 1
    return list(db.scans.find({"status": "done"}).sort("score", order).limit(limit))


def register_leaderboard(app, db):
    """Add the leaderboard page to the app."""

    @app.route("/leaderboard")
    def leaderboard():
        return render_template(
            "leaderboard.html",
            cleanest=top_scans(db),
            messiest=top_scans(db, messiest=True),
        )
