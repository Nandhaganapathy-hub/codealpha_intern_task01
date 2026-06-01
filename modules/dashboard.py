"""
============================================================
DATA REDUNDANCY REMOVAL SYSTEM - Dashboard Module
File: modules/dashboard.py
Purpose: Fetches and computes all statistics shown on the dashboard.
         Queries both the real-time records table and the cached stats table.
============================================================
"""

from modules.db import get_db


def get_dashboard_stats() -> dict:
    """
    Returns a dictionary of all dashboard statistics.
    
    Stats Collected:
    ─────────────────
    From 'dashboard_stats' cache table:
      - total_records   : Total unique records in the system
      - total_unique    : Count of records classified as UNIQUE
      - total_redundant : Count of submissions classified as REDUNDANT
      - total_false_pos : Count of submissions classified as FALSE_POSITIVE

    From 'submission_log' table:
      - recent_submissions: Last 5 submissions with their classification
      - classification_counts: Count per classification for charts
    
    Returns:
        dict: All stats needed to render the dashboard
    """
    db = get_db()
    cursor = db.cursor()

    # ── Cached stat counters ──────────────────
    cursor.execute("SELECT stat_key, stat_value FROM dashboard_stats")
    raw_stats = cursor.fetchall()
    stats = {row["stat_key"]: row["stat_value"] for row in raw_stats}

    # ── Live counts (fallback / verification) ─
    cursor.execute("SELECT COUNT(*) AS cnt FROM records")
    live_records = cursor.fetchone()["cnt"]
    stats["live_records"] = live_records

    # ── Submission log counts per classification ──
    cursor.execute("""
        SELECT classification, COUNT(*) AS cnt
        FROM submission_log
        GROUP BY classification
    """)
    class_counts = cursor.fetchall()
    for row in class_counts:
        stats[f"log_{row['classification'].lower()}"] = row["cnt"]

    # ── Total submissions ─────────────────────
    cursor.execute("SELECT COUNT(*) AS cnt FROM submission_log")
    stats["total_submissions"] = cursor.fetchone()["cnt"]

    # ── Recent 5 submissions ──────────────────
    cursor.execute("""
        SELECT submitted_name, submitted_email, classification,
               similarity_score, submitted_at
        FROM submission_log
        ORDER BY submitted_at DESC
        LIMIT 5
    """)
    stats["recent_submissions"] = cursor.fetchall()

    # ── Top cities in master records ──────────
    cursor.execute("""
        SELECT city, COUNT(*) AS cnt
        FROM records
        WHERE city IS NOT NULL AND city != ''
        GROUP BY city
        ORDER BY cnt DESC
        LIMIT 5
    """)
    stats["top_cities"] = cursor.fetchall()

    # ── Monthly trend (last 6 months) ─────────
    cursor.execute("""
        SELECT strftime('%Y-%m', submitted_at) AS month,
               COUNT(*) AS total,
               SUM(CASE WHEN classification = 'UNIQUE' THEN 1 ELSE 0 END)         AS unique_c,
               SUM(CASE WHEN classification = 'REDUNDANT' THEN 1 ELSE 0 END)      AS redundant_c,
               SUM(CASE WHEN classification = 'FALSE_POSITIVE' THEN 1 ELSE 0 END) AS fp_c
        FROM submission_log
        WHERE submitted_at >= datetime('now', '-6 month')
        GROUP BY month
        ORDER BY month
    """)
    stats["monthly_trend"] = cursor.fetchall()

    cursor.close()

    # ── Calculate duplicate rate ──────────────
    total = stats.get("total_submissions", 0)
    if total > 0:
        dup = stats.get("log_redundant", 0)
        stats["duplicate_rate"] = round((dup / total) * 100, 1)
    else:
        stats["duplicate_rate"] = 0.0

    return stats
