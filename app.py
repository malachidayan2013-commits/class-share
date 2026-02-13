from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret")

DATA_FILE = "data.json"
PASSWORD_FILE = "password.txt"
UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------- DATA ----------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "root": {"type": "folder", "children": {}},
            "trash": {}
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_password():
    if not os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "w") as f:
            f.write("1234")
    with open(PASSWORD_FILE, "r") as f:
        return f.read().strip()


def get_folder_by_path(data, path):
    parts = path.split("/")
    current = None

    for part in parts:
        if part == "root":
            current = data["root"]
        else:
            current = current["children"].get(part)

        if not current or current["type"] != "folder":
            return None

    return current


# ---------------- LOGIN ----------------

@app.route("/")
def home():
    if "role" not in session:
        return render_template("login.html")
    return redirect("/dashboard")


@app.route("/login", methods=["POST"])
def login():
    role = request.form.get("role")

    if role == "student":
        session["role"] = "student"

    elif role == "teacher":
        if request.form.get("password") == get_password():
            session["role"] = "teacher"
        else:
            return render_template("login.html", error="סיסמה שגויה")

    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect("/")

    data = load_data()
    path = request.args.get("path", "root")

    folder = get_folder_by_path(data, path)
    if not folder:
        return redirect("/dashboard?path=root")

    return render_template(
        "dashboard.html",
        role=session["role"],
        folder=folder,
        path=path
    )


# ---------------- CREATE ----------------

@app.route("/create", methods=["POST"])
def create():
    if session.get("role") != "teacher":
        return redirect("/dashboard")

    data = load_data()
    path = request.form.get("path", "root")
    folder = get_folder_by_path(data, path)

    if not folder:
        return redirect("/dashboard")

    item_type = request.form.get("type")
    name = request.form.get("name")

    if not name:
        return redirect(f"/dashboard?path={path}")

    if item_type == "folder":
        folder["children"][name] = {
            "type": "folder",
            "children": {}
        }

    elif item_type == "link":
        url = request.form.get("url")
        folder["children"][name] = {
            "type": "link",
            "url": url
        }

    elif item_type == "file":
        file = request.files["file"]
        if file:
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
            folder["children"][file.filename] = {
                "type": "file"
            }

    save_data(data)
    return redirect(f"/dashboard?path={path}")


# ---------------- DOWNLOAD ----------------

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
