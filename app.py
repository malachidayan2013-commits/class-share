from flask import Flask, render_template, request, redirect, session, send_from_directory
import os
import json
import shutil

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret")

DATA_FILE = "data.json"
PASSWORD_FILE = "password.txt"
UPLOAD_FOLDER = "uploads"
TRASH_FOLDER = "trash_files"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRASH_FOLDER, exist_ok=True)

# ---------- DATA ----------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"root": [], "trash": []}
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

# ---------- LOGIN ----------

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

# ---------- DASHBOARD ----------

@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect("/")
    data = load_data()
    view = request.args.get("view", "files")
    return render_template("dashboard.html",
                           role=session["role"],
                           data=data,
                           view=view)

# ---------- CREATE ----------

@app.route("/create", methods=["POST"])
def create():
    if session.get("role") != "teacher":
        return redirect("/dashboard")

    data = load_data()
    item_type = request.form.get("type")
    name = request.form.get("name")

    if item_type == "folder":
        data["root"].append({"type": "folder", "name": name})

    elif item_type == "link":
        url = request.form.get("url")
        data["root"].append({"type": "link", "name": name, "url": url})

    elif item_type == "file":
        file = request.files["file"]
        if file:
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
            data["root"].append({"type": "file", "name": file.filename})

    save_data(data)
    return redirect("/dashboard")

# ---------- DELETE ----------

@app.route("/delete", methods=["POST"])
def delete():
    if session.get("role") != "teacher":
        return redirect("/dashboard")

    data = load_data()
    name = request.form.get("name")

    item = next((i for i in data["root"] if i["name"] == name), None)
    if item:
        data["root"].remove(item)
        data["trash"].append(item)

        if item["type"] == "file":
            shutil.move(os.path.join(UPLOAD_FOLDER, name),
                        os.path.join(TRASH_FOLDER, name))

    save_data(data)
    return redirect("/dashboard")

@app.route("/restore", methods=["POST"])
def restore():
    if session.get("role") != "teacher":
        return redirect("/dashboard?view=trash")

    data = load_data()
    name = request.form.get("name")

    item = next((i for i in data["trash"] if i["name"] == name), None)
    if item:
        data["trash"].remove(item)
        data["root"].append(item)

        if item["type"] == "file":
            shutil.move(os.path.join(TRASH_FOLDER, name),
                        os.path.join(UPLOAD_FOLDER, name))

    save_data(data)
    return redirect("/dashboard?view=trash")

@app.route("/delete_forever", methods=["POST"])
def delete_forever():
    if session.get("role") != "teacher":
        return redirect("/dashboard?view=trash")

    data = load_data()
    name = request.form.get("name")

    item = next((i for i in data["trash"] if i["name"] == name), None)
    if item:
        data["trash"].remove(item)
        if item["type"] == "file":
            path = os.path.join(TRASH_FOLDER, name)
            if os.path.exists(path):
                os.remove(path)

    save_data(data)
    return redirect("/dashboard?view=trash")

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
