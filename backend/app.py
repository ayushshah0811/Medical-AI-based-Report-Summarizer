import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
import os
import uuid
import threading
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from groq import Groq
from ocr import extract_text

# ---------------------------------------
# APP SETUP
# ---------------------------------------
load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_EXPIRY_HOURS = 24

IST = timezone(timedelta(hours=5, minutes=30))
# ---------------------------------------
# JOB STORE (IN-MEMORY)
# ---------------------------------------
jobs = {}
# jobs[job_id] = {
#   "status": "processing" | "done" | "error",
#   "report_id": None,
#   "error": None
# }

# ---------------------------------------
# DATABASE CONNECTION (RENDER SAFE)
# ---------------------------------------
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ---------------------------------------
# HEALTH CHECK
# ---------------------------------------
@app.route("/ping")
def ping():
    return {"message": "Backend is working!"}

# ---------------------------------------
# BACKGROUND PROCESSOR
# ---------------------------------------
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

def process_document(job_id, filepath, filename):
    try:
        # OCR
        raw_text = extract_text(filepath)

        # AI summary
        summary = generate_summary(raw_text)
        expires_at = datetime.now(IST) + timedelta(hours=12)
        # Save to DB
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO reports (filename, summary, expires_at)
            VALUES (%s, %s, %s)
            RETURNING id, public_id
            """,
            (filename, summary, expires_at)
        )

        row = cur.fetchone()
        if not row:
            raise Exception("Failed to insert report")

        report_id, public_id = row

        conn.commit()
        cur.close()
        conn.close()

        jobs[job_id]["status"] = "done"
        jobs[job_id]["report_id"] = report_id
        jobs[job_id]["public_id"] = str(public_id)

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

# ---------------------------------------
# UPLOAD (FAST RESPONSE)
# ---------------------------------------
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)

    if not allowed_file(filename):
        return jsonify({
            "error": "Invalid file type. Only PDF, PNG, JPG, and JPEG are allowed."
        }), 400
    job_id = str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_FOLDER, f"{job_id}_{filename}")

    file.save(filepath)

    jobs[job_id] = {
        "status": "processing",
        "report_id": None,
        "error": None
    }

    thread = threading.Thread(
        target=process_document,
        args=(job_id, filepath, filename),
        daemon=True
    )
    thread.start()

    return jsonify({
        "job_id": job_id,
        "status": "processing"
    })

# ---------------------------------------
# JOB STATUS (POLLING)
# ---------------------------------------
@app.route("/status/<job_id>")
def job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Invalid job id"}), 404
    return jsonify(job)

# ---------------------------------------
# GPT-BASED MEDICAL SUMMARY
# ---------------------------------------
def generate_summary(raw_text):
    prompt = f"""
You are a highly skilled medical expert.

Below is the OCR-extracted medical report. Analyze this report and create a summary.

You decide the structure, tone, and format — do NOT follow templates.
Focus on: abnormal findings, clinical reasoning, simple patient explanations, immediate next steps, and daily lifestyle dos/don'ts.

OCR TEXT:
{raw_text}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000
    )

    return response.choices[0].message.content


# ---------------------------------------
# USER AUTHENTICATION
# ---------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8")
    )

def generate_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(IST) + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization")

        if not auth or not auth.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401

        token = auth.split(" ")[1]

        try:
            payload = jwt.decode(
                token, JWT_SECRET, algorithms=["HS256"]
            )
            request.user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return wrapper

#---------------------------
# Signup Endpoint
#---------------------------

@app.route("/auth/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        return jsonify({"error": "Email already exists"}), 409

    pwd_hash = hash_password(password)

    cur.execute(
        "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
        (email, pwd_hash)
    )
    user_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    token = generate_token(user_id)

    return jsonify({
        "token": token,
        "user_id": user_id
    })

#--------------------------
# Login Endpoint
#--------------------------

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, password_hash FROM users WHERE email = %s",
        (email,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Invalid credentials"}), 401

    user_id, pwd_hash = row

    if not verify_password(password, pwd_hash):
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token(user_id)

    return jsonify({
        "token": token,
        "user_id": user_id
    })


# ---------------------------------------
# REPORT LIST
# ---------------------------------------

@app.route("/public/report/<uuid:public_id>", methods=["GET"])
def get_public_report(public_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, filename, summary, created_at, expires_at
        FROM reports
        WHERE public_id = %s AND user_id IS NULL
        """,
        (str(public_id),)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Report not found"}), 404

    expires_at = row[4]
    if expires_at and expires_at < datetime.now(IST):
        return jsonify({"error": "This report has expired"}), 410

    return jsonify({
        "id": row[0],
        "filename": row[1],
        "summary": row[2],
        "created_at": row[3]
    })

@app.route("/my-reports", methods=["GET"])
@login_required
def my_reports():
    user_id = request.user_id

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, filename, created_at
        FROM reports
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "filename": r[1],
            "created_at": r[2]
        }
        for r in rows
    ])

@app.route("/report/<int:rid>/attach", methods=["POST"])
@login_required
def attach_report(rid):
    user_id = request.user_id

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE reports
        SET user_id = %s, expires_at = NULL
        WHERE id = %s AND user_id IS NULL
        """,
        (user_id, rid)
    )

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"error": "Report not found or already saved"}), 400

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Report saved successfully"})


# ---------------------------------------
# SINGLE REPORT
# ---------------------------------------
@app.route("/report/<int:rid>", methods=["GET"])
@login_required
def get_private_report(rid):
    user_id = request.user_id

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, filename, summary, created_at
        FROM reports
        WHERE id = %s AND user_id = %s
        """,
        (rid, user_id)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({
        "id": row[0],
        "filename": row[1],
        "summary": row[2],
        "created_at": row[3]
    })
