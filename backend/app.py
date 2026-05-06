# import os
# import shutil
# from flask import Flask, render_template, redirect, url_for, request, send_from_directory

# app = Flask(__name__)

# # Base directory
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# # Paths
# UNKNOWN_FOLDER = os.path.join(BASE_DIR, "data", "unknown")
# FACES_FOLDER = os.path.join(BASE_DIR, "data", "faces")

# os.makedirs(UNKNOWN_FOLDER, exist_ok=True)
# os.makedirs(FACES_FOLDER, exist_ok=True)

# # ============================
# # Home (Dashboard)
# # ============================
# @app.route("/")
# def home():
#     persons = []

#     for person in os.listdir(UNKNOWN_FOLDER):
#         person_path = os.path.join(UNKNOWN_FOLDER, person)

#         if os.path.isdir(person_path):
#             files = os.listdir(person_path)

#             # Filter only image files
#             image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

#             if image_files:
#                 persons.append({
#                     "name": person,
#                     "image": image_files[0]
#                 })

#     # Sort latest first
#     persons = sorted(persons, key=lambda x: x["name"], reverse=True)

#     return render_template("admin.html", persons=persons)


# # ============================
# # Serve Images (IMPORTANT FIX)
# # ============================
# @app.route("/unknown/<person>/<filename>")
# def serve_image(person, filename):
#     folder = os.path.join(UNKNOWN_FOLDER, person)
#     return send_from_directory(folder, filename)


# # ============================
# # Approve Person
# # ============================
# @app.route("/approve/<person>", methods=["POST"])
# def approve(person):
#     person_name = request.form.get("name")

#     src_folder = os.path.join(UNKNOWN_FOLDER, person)
#     dest_folder = os.path.join(FACES_FOLDER, person_name)

#     os.makedirs(dest_folder, exist_ok=True)

#     for file in os.listdir(src_folder):
#         shutil.move(
#             os.path.join(src_folder, file),
#             os.path.join(dest_folder, file)
#         )

#     os.rmdir(src_folder)

#     return redirect(url_for("home"))


# # ============================
# # Reject Person
# # ============================
# @app.route("/reject/<person>")
# def reject(person):
#     folder = os.path.join(UNKNOWN_FOLDER, person)

#     for file in os.listdir(folder):
#         os.remove(os.path.join(folder, file))

#     os.rmdir(folder)

#     return redirect(url_for("home"))


# # ============================
# if __name__ == "__main__":
#     app.run(debug=True)



from datetime import datetime
import subprocess
import os
import shutil
import sqlite3
import bcrypt
from flask import Flask, render_template, redirect, url_for, request, session, send_from_directory

app = Flask(__name__)
app.secret_key = "supersecretkey"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UNKNOWN_FOLDER = os.path.join(BASE_DIR, "data", "unknown")
FACES_FOLDER = os.path.join(BASE_DIR, "data", "faces")

os.makedirs(UNKNOWN_FOLDER, exist_ok=True)
os.makedirs(FACES_FOLDER, exist_ok=True)



LOG_FILE = os.path.join(BASE_DIR, "logs.txt")

def log_event(name, status):
    with open(LOG_FILE, "a") as f:
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{name} - {time_now} - {status}\n")



# ============================
# DATABASE FUNCTIONS
# ============================
def get_user(username):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()

    conn.close()
    return user


def create_user(username, password, role):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, hashed, role)
    )

    conn.commit()
    conn.close()


# ============================
# LOGIN
# ============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode()

        user = get_user(username)

        if user and bcrypt.checkpw(password, user[2]):
            session["user"] = username
            session["role"] = user[3]
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


# ============================
# LOGOUT
# ============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================
# DASHBOARD
# ============================
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    persons = []

    for person in os.listdir(UNKNOWN_FOLDER):
        person_path = os.path.join(UNKNOWN_FOLDER, person)

        if os.path.isdir(person_path):
            files = os.listdir(person_path)
            image_files = [f for f in files if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

            if image_files:
                persons.append({
                    "name": person,
                    "image": image_files[0]
                })

    return render_template("admin.html", persons=persons, role=session["role"])


# ============================
# SERVE IMAGE
# ============================
@app.route("/unknown/<person>/<filename>")
def serve_image(person, filename):
    if "user" not in session:
        return redirect(url_for("login"))

    return send_from_directory(os.path.join(UNKNOWN_FOLDER, person), filename)


# ============================
# APPROVE (ADMIN ONLY)
# ============================
@app.route("/approve/<person>", methods=["POST"])
def approve(person):
    if "user" not in session or session["role"] != "admin":
        return "Unauthorized"

    person_name = request.form.get("name")

    src_folder = os.path.join(UNKNOWN_FOLDER, person)
    dest_folder = os.path.join(FACES_FOLDER, person_name)

    os.makedirs(dest_folder, exist_ok=True)

    for file in os.listdir(src_folder):
        shutil.move(
            os.path.join(src_folder, file),
            os.path.join(dest_folder, file)
        )

    os.rmdir(src_folder)
    log_event(person_name, "APPROVED")
    # 🔥 AUTO RETRAIN MODEL
    print("Retraining model...")
    subprocess.run(["python", "train_model.py"])
    
    return redirect(url_for("home"))

# ============================
# REJECT (ADMIN ONLY)
# ============================
@app.route("/reject/<person>")
def reject(person):
    if "user" not in session or session["role"] != "admin":
        return "Unauthorized"

    folder = os.path.join(UNKNOWN_FOLDER, person)

    for file in os.listdir(folder):
        os.remove(os.path.join(folder, file))

    os.rmdir(folder)
    log_event(person, "REJECTED")
    return redirect(url_for("home"))


# ============================
# ADD USER (ADMIN ONLY)
# ============================
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if "user" not in session or session["role"] != "admin":
        return "Unauthorized"

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        create_user(username, password, role)
        return redirect(url_for("home"))

    return render_template("add_user.html")


# ============================
if __name__ == "__main__":
    app.run(debug=True)