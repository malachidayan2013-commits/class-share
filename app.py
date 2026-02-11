from flask import Flask, render_template, request, redirect, send_from_directory, session
import os
import json

app = Flask(__name__)
app.secret_key = "super_secret_key"

UPLOAD_FOLDER = "uploads"
DATA_FILE = "data.json"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# יצירת קובץ סיסמה אם לא קיים
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"password": "1234"}, f)


def get_password():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["password"]


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
            password = request.form.get("password")
            if password == get_password():
                session["role"] = "teacher"
                return redirect("/")
            else:
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
    return render_template("index.html", files=files, role=session["role"])


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


@app.route("/delete/<filename>")
def delete(filename):
    if session.get("role") != "teacher":
        return "אין הרשאה"

    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)

    return redirect("/")


@app.route("/change_password", methods=["POST"])
def change_password():
    if session.get("role") != "teacher":
        return "אין הרשאה"

    current = request.form["current_password"]
    new = request.form["new_password"]

    if current == get_password():
        set_password(new)
        return redirect("/")
    else:
        return "סיסמה נוכחית שגויה"


if __name__ == "__main__":
    app.run(debug=True)
