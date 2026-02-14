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

def set_password(new_password):
    with open(PASSWORD_FILE, "w") as f:
        f.write(new_password)

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
    return redirect("/dashboard?path=root")

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
    return redirect("/dashboard?path=root")

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
        return redirect("/dashboard?path=root")

    data = load_data()
    path = request.form.get("path")
    folder = get_folder_by_path(data, path)

    item_type = request.form.get("type")
    name = request.form.get("name")

    if item_type == "folder":
        folder["children"][name] = {"type": "folder", "children": {}}

    elif item_type == "link":
        url = request.form.get("url")
        folder["children"][name] = {"type": "link", "url": url}

    elif item_type == "file":
        file = request.files["file"]
        if file:
            file.save(os.path.join(UPLOAD_FOLDER, name))
            folder["children"][name] = {"type": "file"}

    save_data(data)
    return redirect(f"/dashboard?path={path}")

# ---------------- EDIT ----------------

@app.route("/edit")
def edit_page():
    if session.get("role") != "teacher":
        return redirect("/dashboard?path=root")

    data = load_data()
    path = request.args.get("path")
    name = request.args.get("name")

    folder = get_folder_by_path(data, path)
    item = folder["children"].get(name)

    if not item:
        return redirect(f"/dashboard?path={path}")

    return render_template(
        "edit.html",
        item=item,
        name=name,
        path=path
    )


@app.route("/update", methods=["POST"])
def update():
    if session.get("role") != "teacher":
        return redirect("/dashboard?path=root")

    data = load_data()
    path = request.form.get("path")
    old_name = request.form.get("old_name")
    new_name = request.form.get("new_name")

    folder = get_folder_by_path(data, path)
    item = folder["children"].get(old_name)

    if not item:
        return redirect(f"/dashboard?path={path}")

    # ---- תיקייה ----
    if item["type"] == "folder":
        folder["children"][new_name] = item
        if new_name != old_name:
            del folder["children"][old_name]

    # ---- קישור ----
    elif item["type"] == "link":
        item["url"] = request.form.get("url")
        folder["children"][new_name] = item
        if new_name != old_name:
            del folder["children"][old_name]

    # ---- קובץ ----
    elif item["type"] == "file":
        uploaded_file = request.files.get("file")

        if uploaded_file and uploaded_file.filename != "":
            # מוחק קובץ ישן פיזית
            old_path = os.path.join(UPLOAD_FOLDER, old_name)
            if os.path.exists(old_path):
                os.remove(old_path)

            uploaded_file.save(os.path.join(UPLOAD_FOLDER, new_name))

        else:
            # רק שינוי שם
            old_path = os.path.join(UPLOAD_FOLDER, old_name)
            new_path = os.path.join(UPLOAD_FOLDER, new_name)
            if os.path.exists(old_path) and new_name != old_name:
                os.rename(old_path, new_path)

        folder["children"][new_name] = {"type": "file"}

        if new_name != old_name:
            del folder["children"][old_name]

    save_data(data)
    return redirect(f"/dashboard?path={path}")


# ---------------- DELETE → TRASH ----------------

@app.route("/delete")
def delete():
    if session.get("role") != "teacher":
        return redirect("/dashboard?path=root")

    data = load_data()
    path = request.args.get("path")
    name = request.args.get("name")

    folder = get_folder_by_path(data, path)

    if name in folder["children"]:
        data["trash"][name] = folder["children"][name]
        del folder["children"][name]
        save_data(data)

    return redirect(f"/dashboard?path={path}")

# ---------------- TRASH PAGE ----------------

@app.route("/trash")
def trash_page():
    if session.get("role") != "teacher":
        return redirect("/dashboard?path=root")

    data = load_data()
    return render_template("trash.html", trash=data["trash"])

# ---------------- RESTORE ----------------

@app.route("/restore/<name>")
def restore(name):
    if session.get("role") != "teacher":
        return redirect("/dashboard?path=root")

    data = load_data()

    if name in data["trash"]:
        data["root"]["children"][name] = data["trash"][name]
        del data["trash"][name]
        save_data(data)

    return redirect("/trash")

# ---------------- EMPTY TRASH ----------------

@app.route("/empty_trash")
def empty_trash():
    if session.get("role") != "teacher":
        return redirect("/dashboard?path=root")

    data = load_data()
    data["trash"] = {}
    save_data(data)

    return redirect("/trash")

# ---------------- CHANGE PASSWORD ----------------

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if session.get("role") != "teacher":
        return redirect("/dashboard?path=root")

    if request.method == "POST":
        new_password = request.form.get("new_password")
        set_password(new_password)
        return redirect("/dashboard?path=root")

    return render_template("change_password.html")

# ---------------- DOWNLOAD ----------------

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
