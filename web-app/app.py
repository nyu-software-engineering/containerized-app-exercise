import os
import pymongo
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from bson.objectid import ObjectId
import flask_login
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError

load_dotenv()

connection = pymongo.MongoClient(os.getenv("MONGO_URI"))

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

db = connection[os.getenv("MONGO_DBNAME")]

users = db.users
users.create_index("email", unique = True)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    try:
        data = users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None

    if data is None:
        return None

    user = User()
    user.id = str(data["_id"])
    user.username = data["username"]
    user.email = data["email"]
    return user

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]

        data = db.users.find_one({"username": username})

        if data and check_password_hash(data["password_hash"], password):
            user = User()
            user.id = str(data["_id"])
            user.username = data["username"]
            user.email = data["email"]

            flask_login.login_user(user)
            return redirect(url_for("home"))

        return render_template("login.html", error="incorrect email or password")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        username = request.form["username"]

        if not username or not email or not password:
            return render_template("signup.html", error="missing fields")

        if len(password) < 8:
            return render_template("signup.html", error="password must be 8 characters at least")

        try:
            db.users.insert_one({
                "username": username.strip().lower(),
                "email": email,
                "password_hash": generate_password_hash(password)
            })

            return redirect(url_for("login"))

        except DuplicateKeyError:
            return render_template("signup.html", error="user already exists")

    return render_template("signup.html")

@app.route("/home")
@flask_login.login_required
def home():
    return render_template("home.html", username = flask_login.current_user.username)

@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)