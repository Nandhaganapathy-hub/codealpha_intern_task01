"""
============================================================
DATA REDUNDANCY REMOVAL SYSTEM - Database Connection Module
File: modules/db.py
Purpose: Manages SQLite database connection using Flask's
         application context (g) to reuse connections
         within a single request lifecycle.
         Auto-initializes the database if it doesn't exist.
============================================================
"""

import sqlite3
import os
import datetime
from flask import g, current_app
from config import DB_CONFIG


def dict_factory(cursor, row):
    """
    Converts SQLite row results into standard Python dictionaries.
    Automatically parses datetime string fields into Python datetime objects
    to ensure full compatibility with template strftime methods.
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        col_name = col[0]
        val = row[idx]
        if val and isinstance(val, str) and (col_name.endswith("_at") or col_name.endswith("_on") or col_name == "last_updated"):
            try:
                if " " in val:
                    val = datetime.datetime.strptime(val.split(".")[0], "%Y-%m-%d %H:%M:%S")
                elif "T" in val:
                    val = datetime.datetime.fromisoformat(val.split(".")[0])
            except Exception:
                pass
        d[col_name] = val
    return d


def init_db(db_path):
    """
    Checks if the database is initialized. If not, reads
    schema.sql and runs all queries to build tables and seed data.
    """
    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if 'records' table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='records';")
    exists = cursor.fetchone()
    
    if not exists:
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            cursor.executescript(schema_sql)
            conn.commit()
            print("SQLite database successfully auto-initialized and seeded!")
        else:
            print(f"Warning: schema.sql not found at {schema_path}. Database left empty.")
            
    conn.close()


def get_db():
    """
    Returns the database connection for the current request context.
    - If the db file does not exist, it runs the schema script first.
    - Sets row_factory to dict_factory to mimic dictionary cursor.
    - Enables SQLite Foreign Key support.
    """
    if 'db' not in g:
        db_path = DB_CONFIG["database"]
        init_db(db_path)
        
        g.db = sqlite3.connect(db_path)
        g.db.execute("PRAGMA foreign_keys = ON;")
        g.db.row_factory = dict_factory
        
    return g.db


def close_db(e=None):
    """
    Closes the database connection at the end of each request.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_app(app):
    """
    Registers the close_db function with Flask's lifecycle.
    """
    app.teardown_appcontext(close_db)
