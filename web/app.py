import os
import requests

from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)

app.secret_key = os.environ["SECRET_KEY"]

API_URL = os.getenv("API_URL", "http://api:17000")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "false").lower() == "true",
)


def api_headers():
    token = session.get("token")

    if not token:
        return {}

    return {"Authorization": f"Bearer {token}"}


def api_request(method, endpoint, **kwargs):
    try:
        response = requests.request(method, f"{API_URL}{endpoint}", timeout=5, **kwargs)
        return response

    except requests.RequestException:
        return None


def api_json(response):
    if response is None:
        return {}

    try:
        return response.json()
    except ValueError:
        return {}


@app.route("/")
def index():
    page = max(1, request.args.get("page", default=1, type=int) or 1)
    response = api_request("GET", "/notes", params={"page": page, "per_page": 10})
    data = api_json(response) if response and response.ok else {}
    if not isinstance(data, dict):
        data = {}

    total_pages = data.get("total_pages", 0)
    if total_pages and page > total_pages:
        return redirect(url_for("index", page=total_pages))

    notes = data.get("notes", [])
    page_numbers = range(max(1, page - 2), min(total_pages, page + 2) + 1)

    return render_template(
        "notes.html",
        notes=notes,
        page=page,
        total_pages=total_pages,
        total_notes=data.get("total", 0),
        page_numbers=page_numbers,
        has_previous=data.get("has_previous", False),
        has_next=data.get("has_next", False),
        unavailable=not (response and response.ok),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")

        response = api_request(
            "POST", "/users/register", json={"username": username, "password": password}
        )

        if response is None:
            flash("Registration service is unavailable.")
            return render_template("register.html")

        data = api_json(response)

        if response.status_code == 201:
            flash("Account created. You can now log in.")
            return redirect(url_for("login"))

        flash(data.get("error", "Registration failed."))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        response = api_request(
            "POST",
            "/users/login",
            json={
                "username": request.form.get("username", ""),
                "password": request.form.get("password", ""),
            },
        )

        data = api_json(response)

        if response is None:
            flash("Unable to connect to the API.")
            return render_template("login.html")

        if not response.ok:
            flash(data.get("detail", "Invalid username or password."))
            return render_template("login.html")

        session["token"] = data["access_token"]
        session["username"] = data["username"]

        flash("Login successful!")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("index"))


@app.route("/notes", methods=["GET", "POST"])
def notes():
    if not session.get("token"):
        flash("Please log in first.")
        return redirect(url_for("login"))

    if request.method == "POST":
        content = request.form.get("content", "").strip()

        response = api_request(
            "POST", "/notes", json={"content": content}, headers=api_headers()
        )

        data = api_json(response)

        if response is None or not response.ok:
            flash(data.get("detail", "Could not publish note."))
            return render_template("notes/create.html")

        flash("Note published successfully!")
        return redirect(url_for("index"))

    return render_template("notes/create.html")
