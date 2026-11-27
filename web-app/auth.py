"""Register and login pages."""

from flask import redirect, render_template, request, session, url_for

from users import create_user, verify_user


def register_auth(app, db):
    """Add the register and login pages to the app."""

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            try:
                create_user(db, username, password)
            except ValueError as error:
                return render_template("register.html", error=str(error))
            session["user"] = username
            return redirect(url_for("home"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            user = verify_user(db, username, request.form.get("password", ""))
            if user is None:
                return render_template(
                    "login.html", error="Wrong username or password."
                )
            session["user"] = username
            return redirect(url_for("home"))
        return render_template("login.html")
