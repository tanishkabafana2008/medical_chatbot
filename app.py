import io
import os
import sqlite3

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    session,
    send_file,
)
from flask_session import Session
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas

from config import Config
from database import (
    create_database,
    save_chat,
    get_chat_history,
    create_user,
    get_user_by_email,
    create_admin_table,
    create_default_admin,
    get_admin_by_username,
)
from models import User, create_user_table
from knowledge_base import MedicalKnowledge
from chatbot import get_medical_response
from pdf_reader import extract_pdf_text

UPLOAD_FOLDER = os.path.join("uploads", "reports")

app = Flask(__name__)
app.config.from_object(Config)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

Session(app)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Database setup -----------------------------------------------------
create_database()
create_user_table()
create_admin_table()
create_default_admin()

medical_db = MedicalKnowledge()

# --- Login manager -------------------------------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# --- Auth routes -----------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            create_user(username, email, password)
        except sqlite3.IntegrityError:
            return render_template(
                "register.html",
                error="That username or email is already registered."
            )

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user_row = get_user_by_email(email)

        if user_row and check_password_hash(user_row[3], password):
            login_user(User(user_row[0], user_row[1], user_row[2], user_row[3]))
            return redirect("/")

        return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


# --- Main chat routes --------------------------------------------------
@app.route("/")
@login_required
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"response": "Please enter a question."})

    history = session.get("history", [])

    reply = get_medical_response(message, history)

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    history = history[-20:]  # Keep the last 20 messages
    session["history"] = history

    save_chat(message, reply)

    return jsonify({"response": reply})


@app.route("/new_chat", methods=["POST"])
@login_required
def new_chat():
    session["history"] = []
    return jsonify({"status": "success"})


@app.route("/history")
@login_required
def history():
    rows = get_chat_history()

    data = [
        {"user": row[0], "bot": row[1], "time": row[2]}
        for row in rows
    ]

    return jsonify(data)


@app.route("/upload_report", methods=["POST"])
@login_required
def upload_report():
    if "file" not in request.files:
        return jsonify({"response": "No file uploaded"})

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"response": "Please select a PDF"})

    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".pdf"):
        return jsonify({"response": "Please upload a PDF file"})

    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    pdf_text = extract_pdf_text(path)

    prompt = f"""Explain this medical report in simple language.

Do not diagnose.

Explain:
- Important values
- Medical terms
- What the report generally indicates
- Questions a patient may ask a doctor

Report:
{pdf_text}
"""

    explanation = get_medical_response(prompt)

    return jsonify({"response": explanation})


@app.route("/export-chat")
@login_required
def export_chat():
    chats = get_chat_history()

    pdf = io.BytesIO()
    c = canvas.Canvas(pdf)

    y = 800
    c.drawString(50, y, "MediBot AI Chat History")
    y -= 40

    for chat_row in chats:
        text = "User: " + chat_row[0] + "\nAI: " + chat_row[1]

        for line in text.split("\n"):
            c.drawString(50, y, line[:100])
            y -= 20

            if y < 50:
                c.showPage()
                y = 800

    c.save()
    pdf.seek(0)

    return send_file(pdf, download_name="medibot_chat.pdf", as_attachment=True)


# --- Medical reference pages ---------------------------------------------
@app.route("/diseases")
@login_required
def diseases():
    data = medical_db.diseases.to_dict(orient="records")
    return render_template("medical/disease.html", diseases=data)


@app.route("/medicines")
@login_required
def medicines():
    data = medical_db.medicines.to_dict(orient="records")
    return render_template("medical/medicines.html", medicines=data)


@app.route("/first-aid")
@login_required
def first_aid():
    data = medical_db.first_aid.to_dict(orient="records")
    return render_template("medical/first_aid.html", first_aid=data)


@app.route("/nutrition")
@login_required
def nutrition():
    data = medical_db.nutrition.to_dict(orient="records")
    return render_template("medical/nutrition.html", nutrition=data)


# --- Admin routes ----------------------------------------------------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        admin = get_admin_by_username(username)

        if admin and check_password_hash(admin[2], password):
            session["admin"] = admin[0]
            return redirect("/admin-dashboard")

        return render_template("admin/login.html", error="Invalid credentials.")

    return render_template("admin/login.html")


@app.route("/admin-dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin-login")

    return render_template("admin/dashboard.html")


@app.route("/admin-logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin-login")


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
