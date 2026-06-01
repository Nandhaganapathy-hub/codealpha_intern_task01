"""
============================================================
DATA REDUNDANCY REMOVAL SYSTEM - Main Flask Application
File: app.py
Purpose: Registers all routes, initializes Flask app
============================================================
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
import os

# Import our modules
from modules.db import get_db, close_db
from modules.validator import validate_record
from modules.detector import DuplicateDetector
from modules.dashboard import get_dashboard_stats

# ─────────────────────────────────────────────
# Flask App Setup
# ─────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "drrs_secret_key_2024")
CORS(app)

# Register DB teardown (closes connection after every request)
from modules.db import init_app as db_init_app
db_init_app(app)

# Instantiate the duplicate detector (loaded once at startup)
detector = DuplicateDetector()

# ─────────────────────────────────────────────
# ROUTE: Home / Dashboard
# ─────────────────────────────────────────────
@app.route("/")
def index():
    """
    Home page — renders the dashboard with live statistics.
    """
    stats = get_dashboard_stats()
    return render_template("index.html", stats=stats)


# ─────────────────────────────────────────────
# ROUTE: New Record Entry Form
# ─────────────────────────────────────────────
@app.route("/add-record", methods=["GET"])
def add_record_form():
    """
    GET: Display the data entry form.
    """
    return render_template("add_record.html")


# ─────────────────────────────────────────────
# ROUTE: Submit New Record (POST)
# ─────────────────────────────────────────────
@app.route("/submit-record", methods=["POST"])
def submit_record():
    """
    POST: Receives form data, validates it, runs duplicate detection,
    classifies the record, and responds with the result page.
    """
    data = {
        "unique_id": request.form.get("unique_id", "").strip().upper(),
        "full_name": request.form.get("full_name", "").strip(),
        "email":     request.form.get("email", "").strip().lower(),
        "phone":     request.form.get("phone", "").strip(),
        "address":   request.form.get("address", "").strip(),
        "city":      request.form.get("city", "").strip(),
        "state":     request.form.get("state", "").strip(),
        "country":   request.form.get("country", "India").strip(),
    }

    # Step 1: Validate all required fields
    errors = validate_record(data)
    if errors:
        return render_template("add_record.html", errors=errors, form_data=data)

    # Step 2: Run duplicate detection engine
    result = detector.check(data)

    # Step 3: Log this submission attempt
    _log_submission(data, result)

    # Step 4: If UNIQUE → Insert into master records table
    if result["classification"] == "UNIQUE":
        _insert_record(data)
        _update_stats("total_records", +1)
        _update_stats("total_unique", +1)
        flash("✅ Record added successfully as a UNIQUE entry!", "success")
    elif result["classification"] == "REDUNDANT":
        _update_stats("total_redundant", +1)
        flash("⚠️ Duplicate record detected. Entry was NOT added.", "warning")
    else:  # FALSE_POSITIVE
        _update_stats("total_false_pos", +1)
        flash("🔶 Similar record found. Flagged as False Positive.", "info")

    return render_template("result.html", result=result, submitted=data)


# ─────────────────────────────────────────────
# ROUTE: View All Records
# ─────────────────────────────────────────────
@app.route("/records")
def view_records():
    """
    Displays the full master records table.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, unique_id, full_name, email, phone, city, state, created_at
        FROM records
        ORDER BY created_at DESC
    """)
    records = cursor.fetchall()
    cursor.close()
    return render_template("records.html", records=records)


# ─────────────────────────────────────────────
# ROUTE: Submission Log
# ─────────────────────────────────────────────
@app.route("/logs")
def view_logs():
    """
    Displays all submission attempts with their classification.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT sl.*, r.full_name AS matched_name
        FROM submission_log sl
        LEFT JOIN records r ON sl.matched_record_id = r.id
        ORDER BY sl.submitted_at DESC
        LIMIT 200
    """)
    logs = cursor.fetchall()
    cursor.close()
    return render_template("logs.html", logs=logs)


# ─────────────────────────────────────────────
# ROUTE: Search Records (AJAX)
# ─────────────────────────────────────────────
@app.route("/search")
def search_records():
    """
    GET with ?q= parameter. Returns matching records as JSON.
    Used by the frontend search bar via AJAX.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    db = get_db()
    cursor = db.cursor()
    sql = """
        SELECT id, unique_id, full_name, email, phone, city, state
        FROM records
        WHERE full_name   LIKE ?
           OR email       LIKE ?
           OR phone       LIKE ?
           OR unique_id   LIKE ?
           OR city        LIKE ?
        LIMIT 20
    """
    like_q = f"%{query}%"
    cursor.execute(sql, (like_q, like_q, like_q, like_q, like_q))
    results = cursor.fetchall()
    cursor.close()
    return jsonify(results)


# ─────────────────────────────────────────────
# ROUTE: Delete a Record
# ─────────────────────────────────────────────
@app.route("/delete-record/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    """
    POST: Deletes a record from the master table by ID.
    Also decrements the dashboard stats.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
    db.commit()
    cursor.close()
    _update_stats("total_records", -1)
    _update_stats("total_unique", -1)
    flash("🗑️ Record deleted successfully.", "success")
    return redirect(url_for("view_records"))


# ─────────────────────────────────────────────
# ROUTE: API - Dashboard Stats (JSON)
# ─────────────────────────────────────────────
@app.route("/api/stats")
def api_stats():
    """
    Returns dashboard stats as JSON. Used by the chart on the dashboard.
    """
    return jsonify(get_dashboard_stats())


# ─────────────────────────────────────────────
# ROUTE: API - Bulk Check via JSON
# ─────────────────────────────────────────────
@app.route("/api/check", methods=["POST"])
def api_check():
    """
    JSON API endpoint for bulk or programmatic duplicate checking.
    Accepts a JSON body with record fields.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    errors = validate_record(data)
    if errors:
        return jsonify({"errors": errors}), 422

    result = detector.check(data)
    return jsonify(result)


# ─────────────────────────────────────────────
# HELPER FUNCTIONS (private)
# ─────────────────────────────────────────────

def _insert_record(data: dict):
    """
    Inserts a validated unique record into the master 'records' table.
    """
    db = get_db()
    cursor = db.cursor()
    sql = """
        INSERT INTO records (unique_id, full_name, email, phone, address, city, state, country)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (
        data["unique_id"], data["full_name"], data["email"],
        data["phone"],     data["address"],   data["city"],
        data["state"],     data["country"]
    ))
    db.commit()
    cursor.close()


def _log_submission(data: dict, result: dict):
    """
    Logs every submission attempt in 'submission_log' table.
    Regardless of whether it was accepted or rejected.
    """
    db = get_db()
    cursor = db.cursor()
    sql = """
        INSERT INTO submission_log
          (submitted_uid, submitted_name, submitted_email, submitted_phone,
           submitted_addr, classification, match_reason, similarity_score, matched_record_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (
        data["unique_id"],
        data["full_name"],
        data["email"],
        data["phone"],
        data["address"],
        result["classification"],
        result.get("reason", ""),
        result.get("similarity_score", 0.0),
        result.get("matched_id")
    ))
    db.commit()
    cursor.close()


def _update_stats(key: str, delta: int):
    """
    Updates a dashboard stat counter by delta (can be +1 or -1).
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE dashboard_stats
        SET stat_value = MAX(0, stat_value + ?)
        WHERE stat_key = ?
    """, (delta, key))
    db.commit()
    cursor.close()


# ─────────────────────────────────────────────
# App Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  DATA REDUNDANCY REMOVAL SYSTEM")
    print("  Running at http://127.0.0.1:5000")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=5000)
