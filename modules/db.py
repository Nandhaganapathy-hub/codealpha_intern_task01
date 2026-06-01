"""
============================================================
DATA REDUNDANCY REMOVAL SYSTEM - Database Connection Module
File: modules/db.py
Purpose: Manages MySQL database connection using Flask's
         application context (g) to reuse connections
         within a single request lifecycle.
============================================================
"""

import mysql.connector
from flask import g, current_app
from config import DB_CONFIG


def get_db():
    """
    Returns the database connection for the current request context.
    
    How it works:
    - Flask's 'g' is a special object that lives for ONE request.
    - If 'db' is not on 'g' yet, we create a new MySQL connection.
    - If 'db' already exists (from an earlier call in the same request),
      we reuse it — avoids creating multiple connections per request.
    
    Returns:
        mysql.connector.connection: Active MySQL connection object
    """
    if 'db' not in g:
        g.db = mysql.connector.connect(**DB_CONFIG)
    return g.db


def close_db(e=None):
    """
    Closes the database connection at the end of each request.
    
    This function is registered with Flask's teardown_appcontext,
    so it runs automatically after every request, even if an error occurs.
    
    Args:
        e: Exception, if any (Flask passes this automatically)
    """
    db = g.pop('db', None)
    if db is not None and db.is_connected():
        db.close()


def init_app(app):
    """
    Registers the close_db function with Flask's lifecycle.
    Call this once in app.py when setting up the application.
    
    Args:
        app: The Flask application instance
    """
    app.teardown_appcontext(close_db)
