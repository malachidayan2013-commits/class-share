import os
import json
import shutil
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret")

UPLOAD_FOLDER = "uploads"
TRASH_FOLDER = "trash"
DATA_FILE = "data.json"
PASSWORD_FILE = "password.txt"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRASH_FOLDER, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"root": {}, "trash": {}}, f)

if not os.path.exists(PASSWORD_FILE):
    with open(PASSWORD_FILE, "w") as f:
        f.write("1234")


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_password():
    with open(PASSWORD_FILE, "r") as f:
        return f.read().strip()


@app.route("/")
@app.route("/folder/<path:folder>")
def index(folder="root"):
    data = load_data()
    items = data.get(folder, {})
    return render_template("index.html",
                           items=items,
                           folder=folder,
                           role=session.get("role"))


@app.route("/login", methods=["POST"])
def login():
    if request.form.get("password") == get_password():
        session["role"] = "teacher"
    else:
        session["role"] = "student"
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/create", methods=["POST"])
def create():
    if session.get("role") != "teacher":
        return redirect("/")

    data = load_data()
    folder = request.form["folder"]
    name = request.form["name"]
    item_type = request.form["type"]

    if item_type == "folder":
        data[name] = {}
        data[folder][name] = {"type": "folder", "path": name}

    elif item_type == "link":
        url = request.form["url"]
        data[folder][name] = {"type": "link", "url": url}

    elif item_type == "file":
        file = request.files["file"]
        if file:
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
            data[folder][file.filename] = {"type": "file"}

    save_data(data)
    return redirect(url_for("index", folder=folder))


@app.route("/delete/<folder>/<name>")
def delete(folder, name):
    if session.get("role") != "teacher":
        return redirect("/")

    data = load_data()
    item = data[folder].pop(name)
    data["trash"][name] = item
    save_data(data)
    return redirect(url_for("index", folder=folder))


@app.route("/restore/<name>")
def restore(name):
    if session.get("role") != "teacher":
        return redirect("/")

    data = load_data()
    item = data["trash"].pop(name)
    data["root"][name] = item
    save_data(data)
    return redirect("/folder/trash")


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route("/change_password", methods=["POST"])
def change_password():
    if session.get("role") == "teacher":
        if request.form["current"] == get_password():
            with open(PASSWORD_FILE, "w") as f:
                f.write(request.form["new"])
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
