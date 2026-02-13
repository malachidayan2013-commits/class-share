import os
import json
import shutil
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = "secret_key"

UPLOAD_FOLDER = "uploads"
TRASH_FOLDER = "trash"
DATA_FILE = "data.json"
PASSWORD_FILE = "password.txt"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRASH_FOLDER, exist_ok=True)

# יצירת קובץ סיסמה אם לא קיים
if not os.path.exists(PASSWORD_FILE):
    with open(PASSWORD_FILE, "w") as f:
        f.write("1234")

# יצירת קובץ נתונים אם לא קיים
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"root": {}}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_password():
    with open(PASSWORD_FILE, "r") as f:
        return f.read().strip()

@app.route("/")
@app.route("/folder/<path:folder_path>")
def index(folder_path="root"):
    data = load_data()
    folder = data.get(folder_path, {})
    return render_template("index.html",
                           items=folder,
                           folder_path=folder_path,
                           role=session.get("role"))

@app.route("/login", methods=["POST"])
def login():
    password = request.form["password"]
    if password == get_password():
        session["role"] = "teacher"
    else:
        session["role"] = "student"
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/create", methods=["POST"])
def create():
    if session.get("role") != "teacher":
        return redirect(url_for("index"))

    data = load_data()
    folder_path = request.form["folder_path"]
    name = request.form["name"]
    item_type = request.form["type"]

    if folder_path not in data:
        data[folder_path] = {}

    if item_type == "folder":
        data[name] = {}
        data[folder_path][name] = {"type": "folder", "path": name}

    elif item_type == "link":
        url = request.form["url"]
        data[folder_path][name] = {"type": "link", "url": url}

    elif item_type == "file":
        file = request.files["file"]
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
        data[folder_path][file.filename] = {"type": "file"}

    save_data(data)
    return redirect(url_for("index", folder_path=folder_path))

@app.route("/delete/<folder_path>/<item>")
def delete(folder_path, item):
    if session.get("role") != "teacher":
        return redirect(url_for("index"))

    data = load_data()
    if folder_path in data and item in data[folder_path]:
        data["trash"] = data.get("trash", {})
        data["trash"][item] = data[folder_path][item]
        del data[folder_path][item]
        save_data(data)

    return redirect(url_for("index", folder_path=folder_path))

@app.route("/restore/<item>")
def restore(item):
    if session.get("role") != "teacher":
        return redirect(url_for("index"))

    data = load_data()
    if "trash" in data and item in data["trash"]:
        data["root"][item] = data["trash"][item]
        del data["trash"][item]
        save_data(data)

    return redirect(url_for("index"))

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route("/change_password", methods=["POST"])
def change_password():
    if session.get("role") != "teacher":
        return redirect(url_for("index"))

    current = request.form["current"]
    new = request.form["new"]

    if current == get_password():
        with open(PASSWORD_FILE, "w") as f:
            f.write(new)

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
