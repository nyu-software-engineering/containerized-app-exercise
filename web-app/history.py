"""History page showing a user's past desk scans."""

from flask import redirect, render_template, session


def user_scans(db, username):
    """Return a user's finished scans, newest first."""
    return list(
        db.scans.find({"user": username, "status": "done"}).sort("created_at", -1)
    )


def register_history(app, db):
    """Add the history page to the app."""

    @app.route("/history")
    def history():
        username = session.get("user")
        if username is None:
            return redirect("/login")
        return render_template(
            "history.html", username=username, scans=user_scans(db, username)
        )
