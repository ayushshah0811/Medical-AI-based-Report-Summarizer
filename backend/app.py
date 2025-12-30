import os
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
CORS(app)                # Simple global CORS

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)   

client = Groq(api_key=os.getenv("GROQ_API_KEY"))        

# ---------------------------------------
# DATABASE CONNECTION
# ---------------------------------------
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="medical_reports",
        user="ayushshah",
        password="08112003"   # update this
    )

@app.route("/ping")
def ping():
    return {"message": "Backend is working!"}

@app.route("/upload", methods=["POST"])
def upload():
    # Ensure file exists
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # ---------------------------------------
    # OCR → RAW TEXT
    # ---------------------------------------
    raw_text = extract_text(filepath)

    # ---------------------------------------
    # AI SUMMARY (ChatGPT-style, fully autonomous)
    # ---------------------------------------
    summary = generate_summary(raw_text)

    # ---------------------------------------
    # SAVE TO DATABASE
    # ---------------------------------------
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

    # ---------------------------------------
    # RESPONSE
    # ---------------------------------------
    return jsonify({
        "message": "File processed successfully",
        "filename": filename,
        "path": filepath,
        "summary": summary,
        "report_id": report_id
    })


# ---------------------------------------
# GPT-BASED SMART MEDICAL SUMMARY
# ---------------------------------------
def generate_summary(raw_text):
    prompt = f"""
You are a highly skilled medical expert.

Below is the OCR-extracted medical report. Generate a fully autonomous medical summary.
You decide the structure, tone, and format — do NOT follow templates or fixed sections.

Focus on:
- interpreting key abnormalities
- medical reasoning
- explaining relevance in simple language
- giving natural, human-like summaries

OCR TEXT:
{raw_text}
"""

    try:
        response = client.chat.completions.create(
            model="groq/compound",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI summary unavailable due to error: {str(e)}"


# ---------------------------------------
# GET LIST OF REPORTS
# ---------------------------------------
@app.route("/reports", methods=["GET"])
def get_reports():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, filename, created_at FROM reports ORDER BY created_at DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {"id": r[0], "filename": r[1], "created_at": r[2]}
        for r in rows
    ])


# ---------------------------------------
# GET SINGLE REPORT DETAILS
# ---------------------------------------
@app.route("/report/<int:rid>", methods=["GET"])
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


# ---------------------------------------
# RUN SERVER
# ---------------------------------------
if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
