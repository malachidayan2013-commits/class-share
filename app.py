from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ===============================
# הגדרת תיקיית uploads נכון
# ===============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===============================
# דף ראשי
# ===============================

@app.route("/")
def index():
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return render_template("index.html", files=files)

# ===============================
# העלאת קובץ
# ===============================

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file or file.filename == "":
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)

    if filename == "":
        filename = "file"

    unique_name = str(uuid.uuid4()) + "_" + filename
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_name))

    return redirect(url_for("index"))

# ===============================
# שינוי שם קובץ (מתוקן נכון)
# ===============================

@app.route("/rename", methods=["POST"])
def rename():
    old_name = request.form.get("old_name")
    new_name = request.form.get("new_name")

    if not old_name or not new_name:
        return redirect(url_for("index"))

    old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_name)

    if not os.path.exists(old_path):
        return redirect(url_for("index"))

    # שומרים סיומת מקורית!
    _, ext = os.path.splitext(old_name)

    cleaned_name = secure_filename(new_name)

    if cleaned_name == "":
        cleaned_name = "file"

    new_filename = cleaned_name + ext
    new_path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)

    os.rename(old_path, new_path)

    return redirect(url_for("index"))

# ===============================
# הורדת קובץ
# ===============================

@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
    )

# ===============================

if __name__ == "__main__":
    app.run(debug=True)
