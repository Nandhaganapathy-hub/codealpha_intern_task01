import sqlite3
import os
from config import DB_CONFIG

def test_connection():
    db_path = DB_CONFIG["database"]
    print("--- DB Diagnostic Tool (SQLite) ---")
    print(f"Database Path: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        print("[OK] SUCCESS: Connected to SQLite database.")
        
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        table_names = [t[0] for t in tables if t[0] != 'sqlite_sequence']
        
        if not table_names:
            print("[WARN] WARNING: Connection successful, but NO TABLES found. Triggering auto-initialization...")
            from modules.db import init_db
            init_db(db_path)
            
            # Query again
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_names = [t[0] for t in tables if t[0] != 'sqlite_sequence']
            
        print(f"[OK] FOUND {len(table_names)} tables: {table_names}")
        
        for name in table_names:
            cursor.execute(f"SELECT COUNT(*) FROM {name}")
            cnt = cursor.fetchone()[0]
            print(f"   - Table '{name}': {cnt} records")
            
        conn.close()
    except Exception as err:
        print(f"[FAIL] ERROR DETECTED:")
        print(f"   -> {err}")

if __name__ == "__main__":
    test_connection()
