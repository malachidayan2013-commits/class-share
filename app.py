from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import json
import shutil

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret")

DATA_FILE = "data.json"
PASSWORD_FILE = "password.txt"
UPLOAD_FOLDER = "uploads"
TRASH_FOLDER = "trash"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRASH_FOLDER, exist_ok=True)

# ---------- עזרה ----------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"root": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_password():
    if not os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "w") as f:
            f.write("1234")
    with open(PASSWORD_FILE, "r") as f:
        return f.read().strip()

# ---------- דפים ----------

@app.route("/")
def index():
    data = load_data()
    folder = request.args.get("folder", "root")
    items = data.get(folder, [])
    return render_template("index.html",
                           items=items,
                           folder=folder,
                           role=session.get("role"),
                           trash=data.get("trash", []))

@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password")
    if password == get_password():
        session["role"] = "teacher"
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/new", methods=["POST"])
def new_item():
    if session.get("role") != "teacher":
        return redirect("/")

    data = load_data()
    folder = request.form.get("folder")
    item_type = request.form.get("type")
    name = request.form.get("name")

    if item_type == "folder":
        data[name] = []
        data[folder].append({"type": "folder", "name": name})

    elif item_type == "link":
        url = request.form.get("url")
        data[folder].append({"type": "link", "name": name, "url": url})

    elif item_type == "file":
        file = request.files["file"]
        if file:
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
            data[folder].append({"type": "file", "name": file.filename})

    save_data(data)
    return redirect(f"/?folder={folder}")

@app.route("/delete", methods=["POST"])
def delete():
    if session.get("role") != "teacher":
        return redirect("/")

    data = load_data()
    folder = request.form.get("folder")
    name = request.form.get("name")

    item = next((i for i in data[folder] if i["name"] == name), None)
    if item:
        data[folder].remove(item)
        data.setdefault("trash", []).append(item)

    save_data(data)
    return redirect(f"/?folder={folder}")

@app.route("/restore", methods=["POST"])
def restore():
    if session.get("role") != "teacher":
        return redirect("/")

    data = load_data()
    name = request.form.get("name")

    item = next((i for i in data.get("trash", []) if i["name"] == name), None)
    if item:
        data["trash"].remove(item)
        data["root"].append(item)

    save_data(data)
    return redirect("/")

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
