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

        # Save to DB
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO reports (filename, summary)
            VALUES (%s, %s)
            RETURNING id
            """,
            (filename, summary)
        )
        report_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        jobs[job_id]["status"] = "done"
        jobs[job_id]["report_id"] = report_id

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
# REPORT LIST
# ---------------------------------------
@app.route("/reports")
def get_reports():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, filename, created_at
        FROM reports
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {"id": r[0], "filename": r[1], "created_at": r[2]}
        for r in rows
    ])

# ---------------------------------------
# SINGLE REPORT
# ---------------------------------------
@app.route("/report/<int:rid>")
def get_report(rid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, filename, summary, created_at
        FROM reports
        WHERE id = %s
    """, (rid,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Report not found"}), 404

    return jsonify({
        "id": row[0],
        "filename": row[1],
        "summary": row[2],
        "created_at": row[3]
    })
