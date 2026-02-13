diff --git a/app.py b/app.py
index 5d365893bc7de6594f39062653b8371ab66f6460..a36f40665097bb441c2d6b582b55a79227da7d5f 100644
--- a/app.py
+++ b/app.py
@@ -1,139 +1,294 @@
-import os
 import json
-import shutil
-from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
+import os
+import uuid
+from datetime import datetime
+from pathlib import Path
+
+from flask import (
+    Flask,
+    redirect,
+    render_template,
+    request,
+    send_from_directory,
+    session,
+    url_for,
+)
+from werkzeug.utils import secure_filename
 
 app = Flask(__name__)
 app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret")
 
-UPLOAD_FOLDER = "uploads"
-TRASH_FOLDER = "trash"
-DATA_FILE = "data.json"
-PASSWORD_FILE = "password.txt"
-
-os.makedirs(UPLOAD_FOLDER, exist_ok=True)
-os.makedirs(TRASH_FOLDER, exist_ok=True)
-
-if not os.path.exists(DATA_FILE):
-    with open(DATA_FILE, "w", encoding="utf-8") as f:
-        json.dump({"root": {}, "trash": {}}, f)
-
-if not os.path.exists(PASSWORD_FILE):
-    with open(PASSWORD_FILE, "w") as f:
-        f.write("1234")
+UPLOAD_FOLDER = Path("uploads")
+DATA_FILE = Path("data.json")
+PASSWORD_FILE = Path("password.txt")
+
+UPLOAD_FOLDER.mkdir(exist_ok=True)
+
+
+def default_data():
+    return {
+        "tree": {"type": "folder", "name": "root", "children": {}},
+        "trash": {},
+    }
+
+
+def migrate_data_structure(data):
+    if "tree" in data and "trash" in data:
+        return data
+
+    root_children = {}
+    for key, value in data.get("root", {}).items():
+        if isinstance(value, dict):
+            if value.get("type") == "folder":
+                root_children[key] = {
+                    "type": "folder",
+                    "name": key,
+                    "children": {},
+                }
+            elif value.get("type") == "file":
+                root_children[key] = {
+                    "type": "file",
+                    "name": key,
+                    "stored_name": key,
+                }
+            elif value.get("type") == "link":
+                root_children[key] = {
+                    "type": "link",
+                    "name": key,
+                    "url": value.get("url", "#"),
+                }
+
+    return {
+        "tree": {"type": "folder", "name": "root", "children": root_children},
+        "trash": {},
+    }
+
+
+def ensure_files_exist():
+    if not DATA_FILE.exists():
+        save_data(default_data())
+    if not PASSWORD_FILE.exists():
+        PASSWORD_FILE.write_text("1234", encoding="utf-8")
 
 
 def load_data():
-    with open(DATA_FILE, "r", encoding="utf-8") as f:
-        return json.load(f)
+    ensure_files_exist()
+    with DATA_FILE.open("r", encoding="utf-8") as f:
+        raw = json.load(f)
+    data = migrate_data_structure(raw)
+    if data != raw:
+        save_data(data)
+    return data
 
 
 def save_data(data):
-    with open(DATA_FILE, "w", encoding="utf-8") as f:
-        json.dump(data, f, ensure_ascii=False, indent=4)
+    with DATA_FILE.open("w", encoding="utf-8") as f:
+        json.dump(data, f, ensure_ascii=False, indent=2)
 
 
 def get_password():
-    with open(PASSWORD_FILE, "r") as f:
-        return f.read().strip()
+    ensure_files_exist()
+    return PASSWORD_FILE.read_text(encoding="utf-8").strip()
+
+
+def is_teacher():
+    return session.get("role") == "teacher"
+
+
+def split_path(folder_path):
+    if not folder_path:
+        return []
+    return [segment for segment in folder_path.split("/") if segment]
+
+
+def get_folder_node(tree, folder_path):
+    node = tree
+    for segment in split_path(folder_path):
+        next_node = node["children"].get(segment)
+        if not next_node or next_node.get("type") != "folder":
+            return None
+        node = next_node
+    return node
+
+
+def unique_child_name(children, base_name):
+    if base_name not in children:
+        return base_name
+
+    stem = base_name
+    suffix = 1
+    while f"{stem} ({suffix})" in children:
+        suffix += 1
+    return f"{stem} ({suffix})"
+
+
+def build_breadcrumbs(folder_path):
+    crumbs = [{"name": "ראשי", "path": ""}]
+    current = []
+    for segment in split_path(folder_path):
+        current.append(segment)
+        crumbs.append({"name": segment, "path": "/".join(current)})
+    return crumbs
 
 
 @app.route("/")
 def index():
-    print("SESSION:", session)
-    print("ROLE:", session.get("role"))
-    return render_template("index.html", role=session.get("role"))
+    return redirect(url_for("folder_view", folder_path=""))
 
-@app.route("/folder/<path:folder>")
-def index(folder="root"):
+
+@app.route("/folder/", defaults={"folder_path": ""})
+@app.route("/folder/<path:folder_path>")
+def folder_view(folder_path):
+    data = load_data()
+    folder = get_folder_node(data["tree"], folder_path)
+    if folder is None:
+        return redirect(url_for("folder_view", folder_path=""))
+
+    items = sorted(folder["children"].values(), key=lambda i: (i["type"] != "folder", i["name"].lower()))
+    return render_template(
+        "index.html",
+        items=items,
+        folder_path=folder_path,
+        breadcrumbs=build_breadcrumbs(folder_path),
+        role=session.get("role", "student"),
+        trash_count=len(data["trash"]),
+    )
+
+
+@app.route("/trash")
+def trash_view():
     data = load_data()
-    items = data.get(folder, {})
-    return render_template("index.html",
-                           items=items,
-                           folder=folder,
-                           role=session.get("role"))
+    trash_items = sorted(data["trash"].values(), key=lambda i: i.get("deleted_at", ""), reverse=True)
+    return render_template(
+        "index.html",
+        items=[],
+        trash_items=trash_items,
+        folder_path="",
+        breadcrumbs=[{"name": "ראשי", "path": ""}, {"name": "אשפה", "path": None}],
+        role=session.get("role", "student"),
+        trash_count=len(data["trash"]),
+        is_trash=True,
+    )
 
 
 @app.route("/login", methods=["POST"])
 def login():
     if request.form.get("password") == get_password():
         session["role"] = "teacher"
-    else:
-        session["role"] = "student"
-    return redirect("/")
+    return redirect(request.referrer or url_for("folder_view", folder_path=""))
 
 
 @app.route("/logout")
 def logout():
     session.clear()
-    return redirect("/")
+    return redirect(url_for("folder_view", folder_path=""))
 
 
 @app.route("/create", methods=["POST"])
-def create():
-    if session.get("role") != "teacher":
-        return redirect("/")
+def create_item():
+    if not is_teacher():
+        return redirect(url_for("folder_view", folder_path=""))
 
     data = load_data()
-    folder = request.form["folder"]
-    name = request.form["name"]
-    item_type = request.form["type"]
+    folder_path = request.form.get("folder_path", "")
+    item_type = request.form.get("type")
+    folder = get_folder_node(data["tree"], folder_path)
+    if folder is None:
+        return redirect(url_for("folder_view", folder_path=""))
 
     if item_type == "folder":
-        data[name] = {}
-        data[folder][name] = {"type": "folder", "path": name}
+        raw_name = request.form.get("name", "").strip()
+        if raw_name:
+            name = unique_child_name(folder["children"], raw_name)
+            folder["children"][name] = {"type": "folder", "name": name, "children": {}}
 
     elif item_type == "link":
-        url = request.form["url"]
-        data[folder][name] = {"type": "link", "url": url}
+        raw_name = request.form.get("name", "").strip()
+        url = request.form.get("url", "").strip()
+        if raw_name and url:
+            name = unique_child_name(folder["children"], raw_name)
+            folder["children"][name] = {"type": "link", "name": name, "url": url}
 
     elif item_type == "file":
-        file = request.files["file"]
-        if file:
-            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
-            data[folder][file.filename] = {"type": "file"}
+        uploaded_file = request.files.get("file")
+        if uploaded_file and uploaded_file.filename:
+            original_name = secure_filename(uploaded_file.filename)
+            if original_name:
+                file_name = unique_child_name(folder["children"], original_name)
+                ext = Path(original_name).suffix
+                stored_name = f"{uuid.uuid4().hex}{ext}"
+                uploaded_file.save(UPLOAD_FOLDER / stored_name)
+                folder["children"][file_name] = {
+                    "type": "file",
+                    "name": file_name,
+                    "stored_name": stored_name,
+                }
 
     save_data(data)
-    return redirect(url_for("index", folder=folder))
+    return redirect(url_for("folder_view", folder_path=folder_path))
 
 
-@app.route("/delete/<folder>/<name>")
-def delete(folder, name):
-    if session.get("role") != "teacher":
-        return redirect("/")
+@app.route("/delete", methods=["POST"])
+def move_to_trash():
+    if not is_teacher():
+        return redirect(url_for("folder_view", folder_path=""))
 
     data = load_data()
-    item = data[folder].pop(name)
-    data["trash"][name] = item
+    folder_path = request.form.get("folder_path", "")
+    item_name = request.form.get("item_name", "")
+    folder = get_folder_node(data["tree"], folder_path)
+    if folder is None or item_name not in folder["children"]:
+        return redirect(url_for("folder_view", folder_path=folder_path))
+
+    item = folder["children"].pop(item_name)
+    trash_id = uuid.uuid4().hex
+    data["trash"][trash_id] = {
+        "id": trash_id,
+        "item": item,
+        "original_parent": folder_path,
+        "deleted_at": datetime.utcnow().isoformat(),
+    }
     save_data(data)
-    return redirect(url_for("index", folder=folder))
+    return redirect(url_for("folder_view", folder_path=folder_path))
 
 
-@app.route("/restore/<name>")
-def restore(name):
-    if session.get("role") != "teacher":
-        return redirect("/")
+@app.route("/restore/<trash_id>", methods=["POST"])
+def restore(trash_id):
+    if not is_teacher():
+        return redirect(url_for("folder_view", folder_path=""))
 
     data = load_data()
-    item = data["trash"].pop(name)
-    data["root"][name] = item
+    trash_item = data["trash"].pop(trash_id, None)
+    if not trash_item:
+        return redirect(url_for("trash_view"))
+
+    parent = get_folder_node(data["tree"], trash_item.get("original_parent", ""))
+    if parent is None:
+        parent = data["tree"]
+
+    item = trash_item["item"]
+    restored_name = unique_child_name(parent["children"], item["name"])
+    item["name"] = restored_name
+    parent["children"][restored_name] = item
+
     save_data(data)
-    return redirect("/folder/trash")
+    return redirect(url_for("trash_view"))
 
 
-@app.route("/download/<filename>")
-def download(filename):
-    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
+@app.route("/download/<path:stored_name>")
+def download(stored_name):
+    return send_from_directory(UPLOAD_FOLDER, stored_name, as_attachment=True)
 
 
 @app.route("/change_password", methods=["POST"])
 def change_password():
-    if session.get("role") == "teacher":
-        if request.form["current"] == get_password():
-            with open(PASSWORD_FILE, "w") as f:
-                f.write(request.form["new"])
-    return redirect("/")
+    if is_teacher():
+        current_password = request.form.get("current", "")
+        new_password = request.form.get("new", "").strip()
+        if current_password == get_password() and new_password:
+            PASSWORD_FILE.write_text(new_password, encoding="utf-8")
+    return redirect(request.referrer or url_for("folder_view", folder_path=""))
 
 
 if __name__ == "__main__":
     app.run(debug=True)
