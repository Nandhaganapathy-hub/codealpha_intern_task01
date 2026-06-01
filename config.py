"""
============================================================
DATA REDUNDANCY REMOVAL SYSTEM - Configuration File
File: config.py
Purpose: Central location for all environment settings,
         database credentials, and system thresholds.
         *** CHANGE DB_CONFIG BEFORE RUNNING ***
============================================================
"""

import os

# ─────────────────────────────────────────────
# DATABASE CONFIGURATION
# Update these values with YOUR MySQL credentials
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST",     "localhost"),
    "user":     os.environ.get("DB_USER",     "root"),       # <-- Change this
    "password": os.environ.get("DB_PASSWORD", "Nandharoot@1"),       # <-- Change this
    "database": os.environ.get("DB_NAME",     "data_redundancy_db"),
    "port":     int(os.environ.get("DB_PORT", 3306)),
    "charset":  "utf8mb4",
    "autocommit": False,
    "connection_timeout": 30
}

# ─────────────────────────────────────────────
# DUPLICATE DETECTION THRESHOLDS
# ─────────────────────────────────────────────

# Score (0-100) above which a record is marked REDUNDANT
# 95 means 95% similar — very strict threshold
DUPLICATE_THRESHOLD = 95

# Score (0-100) above which a record is marked FALSE_POSITIVE  
# 75 means 75% similar — moderate threshold
FALSE_POSITIVE_THRESHOLD = 75

# ─────────────────────────────────────────────
# FLASK CONFIG
# ─────────────────────────────────────────────
SECRET_KEY   = os.environ.get("SECRET_KEY", "drrs-intern-secret-2024")
DEBUG        = os.environ.get("FLASK_DEBUG", "True") == "True"
HOST         = "0.0.0.0"
PORT         = int(os.environ.get("PORT", 5000))

# ─────────────────────────────────────────────
# UPLOAD CONFIG (for future CSV upload feature)
# ─────────────────────────────────────────────
UPLOAD_FOLDER     = "uploads"
ALLOWED_EXTENSIONS = {"csv", "xlsx"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB limit
