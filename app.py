from flask import Flask, render_template, request, redirect, send_from_directory, session
import os
import json
import shutil

app = Flask(__name__)
app.secret_key = "super_secret_key"

UPLOAD_FOLDER = "uploads"
DATA_FILE = "data.json"
LINKS_FILE = "links.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# יצירת קובץ סיסמה אם לא קיים
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"password": "1234"}, f)

# יצירת קובץ קישורים אם לא קיים
if not os.path.exists(LINKS_FILE):
    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)


def get_password():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["password"]


def set_password(new_password):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"password": new_password}, f)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")

        if role == "student":
            session["role"] = "student"
            return redirect("/")

        if role == "teacher":
            if request.form.get("password") == get_password():
                session["role"] = "teacher"
                return redirect("/")
            return "סיסמה שגויה"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
def index():
    if "role" not in session:
        return redirect("/login")

    files = os.listdir(UPLOAD_FOLDER)

    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        links = json.load(f)

    return render_template("index.html", files=files, links=links, role=session["role"])


@app.route("/upload", methods=["POST"])
def upload():
    if session.get("role") != "teacher":
        return "אין הרשאה"

    file = request.files["file"]
    if file:
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))

    return redirect("/")


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route("/create_folder", methods=["POST"])
def create_folder():
    if session.get("role") != "teacher":
        return "אין הרשאה"

    folder_name = request.form["folder_name"]
    os.makedirs(os.path.join(UPLOAD_FOLDER, folder_name), exist_ok=True)
    return redirect("/")


@app.route("/create_link", methods=["POST"])
def create_link():
    if session.get("role") != "teacher":
        return "אין הרשאה"

    link_name = request.form["link_name"]
    url = request.form["url"]

    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        links = json.load(f)

    links.append({"name": link_name, "url": url})

    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=4)

    return redirect("/")


@app.route("/delete_file/<filename>")
def delete_file(filename):
    if session.get("role") != "teacher":
        return "אין הרשאה"

    path = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

    return redirect("/")


@app.route("/delete_link/<name>")
def delete_link(name):
    if session.get("role") != "teacher":
        return "אין הרשאה"

    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        links = json.load(f)

    links = [l for l in links if l["name"] != name]

    with open(LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=4)

    return redirect("/")


@app.route("/rename", methods=["POST"])
def rename():
    if session.get("role") != "teacher":
        return "אין הרשאה"

    old_name = request.form["old_name"]
    new_name = request.form["new_name"]

    old_path = os.path.join(UPLOAD_FOLDER, old_name)
    new_path = os.path.join(UPLOAD_FOLDER, new_name)

    if os.path.exists(old_path):
        os.rename(old_path, new_path)

    return redirect("/")


@app.route("/change_password", methods=["POST"])
def change_password():
    if session.get("role") != "teacher":
        return "אין הרשאה"

    if request.form["current_password"] == get_password():
        set_password(request.form["new_password"])
        return redirect("/")

    return "סיסמה נוכחית שגויה"


if __name__ == "__main__":
    app.run(debug=True)
