from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# ===== הגדרות =====
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# יצירת תיקיית uploads אם לא קיימת
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===== דף ראשי =====
@app.route("/")
def index():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template("index.html", files=files)

# ===== העלאת קובץ =====
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return redirect(url_for("index"))

    file = request.files["file"]

    if file.filename == "":
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    return redirect(url_for("index"))

# ===== הורדת קובץ (החלק שהיה שבור) =====
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
    )

# ===== מחיקת קובץ (אופציונלי אבל שימושי) =====
@app.route("/delete/<filename>")
def delete(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        os.remove(path)
    return redirect(url_for("index"))

# ===== הרצה =====
if __name__ == "__main__":
    app.run(debug=True)
