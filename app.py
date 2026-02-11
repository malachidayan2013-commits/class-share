from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os

app = Flask(__name__)

# ================================
# הגדרת תיקיית uploads בצורה נכונה ל-Render
# ================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# יוצר את התיקייה אם היא לא קיימת
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================================
# דף ראשי
# ================================

@app.route("/")
def index():
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    return render_template("index.html", files=files)

# ================================
# העלאת קובץ
# ================================

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return redirect(url_for("index"))

    file = request.files["file"]

    if file.filename == "":
        return redirect(url_for("index"))

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    return redirect(url_for("index"))

# ================================
# הורדת קובץ
# ================================

@app.route("/download/<path:filename>")
def download(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(file_path):
        return "File not found", 404

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
    )

# ================================

if __name__ == "__main__":
    app.run(debug=True)
