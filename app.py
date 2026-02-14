import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = "12345"

UPLOAD_FOLDER = "uploads"
DATA_FILE = "data.json"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    role = request.form.get("role")
    password = request.form.get("password")

    if role == "teacher" and password == "1234":
        session["role"] = "teacher"
        return redirect(url_for("dashboard"))

    if role == "student":
        session["role"] = "student"
        return redirect(url_for("dashboard"))

    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    data = load_data()
    trash_mode = request.args.get("trash")

    if trash_mode:
        items = [x for x in data if x.get("deleted")]
    else:
        items = [x for x in data if not x.get("deleted")]

    return render_template("dashboard.html", items=items, trash=trash_mode)


@app.route("/upload", methods=["POST"])
def upload():
    if session.get("role") != "teacher":
        return redirect(url_for("dashboard"))

    name = request.form.get("name")
    file = request.files.get("file")

    if file:
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))

        data = load_data()
        data.append({
            "id": len(data) + 1,
            "name": name,
            "filename": file.filename,
            "deleted": False
        })
        save_data(data)

    return redirect(url_for("dashboard"))


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route("/delete/<int:item_id>")
def delete(item_id):
    data = load_data()
    for item in data:
        if item["id"] == item_id:
            item["deleted"] = True
    save_data(data)
    return redirect(url_for("dashboard"))


@app.route("/restore/<int:item_id>")
def restore(item_id):
    data = load_data()
    for item in data:
        if item["id"] == item_id:
            item["deleted"] = False
    save_data(data)
    return redirect(url_for("dashboard", trash=1))


if __name__ == "__main__":
    app.run(debug=True)
