from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecret"

DATA_FILE = "data.json"
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"files": [], "trash": []}, f)

def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    data = load_data()
    folder = request.args.get("folder", "")
    return render_template("dashboard.html", 
                           files=data["files"],
                           trash=data["trash"],
                           folder=folder)

@app.route("/create", methods=["POST"])
def create():
    data = load_data()
    item_type = request.form["type"]
    name = request.form["name"]

    new_item = {
        "id": len(data["files"]) + 1,
        "type": item_type,
        "name": name,
        "folder": request.form.get("folder", "")
    }

    if item_type == "file":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        new_item["filename"] = filename

    if item_type == "link":
        new_item["url"] = request.form["url"]

    data["files"].append(new_item)
    save_data(data)

    return redirect(url_for("dashboard"))

@app.route("/delete/<int:item_id>")
def delete(item_id):
    data = load_data()
    for item in data["files"]:
        if item["id"] == item_id:
            data["files"].remove(item)
            data["trash"].append(item)
            break
    save_data(data)
    return redirect(url_for("dashboard"))

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

@app.route("/edit/<int:item_id>", methods=["POST"])
def edit(item_id):
    data = load_data()
    for item in data["files"]:
        if item["id"] == item_id:
            item["name"] = request.form["name"]

            if item["type"] == "link":
                item["url"] = request.form["url"]

            if item["type"] == "file" and "file" in request.files:
                file = request.files["file"]
                if file.filename != "":
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    item["filename"] = filename
            break

    save_data(data)
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
