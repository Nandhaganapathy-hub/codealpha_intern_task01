import mysql.connector
from config import DB_CONFIG

def test_connection():
    print("--- 🔍 Database Diagnostic Tool ---")
    print(f"Attempting to connect to: {DB_CONFIG['host']} as {DB_CONFIG['user']}")
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✅ SUCCESS: Connected to MySQL database.")
        
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if not tables:
            print("⚠️ WARNING: Connection successful, but NO TABLES found. Did you run schema.sql?")
        else:
            print(f"✅ FOUND {len(tables)} tables: {[t[0] for t in tables]}")
            
        conn.close()
    except mysql.connector.Error as err:
        print(f"❌ ERROR DETECTED:")
        if err.errno == 2003:
            print("   -> MySQL Server is not running. Please start your MySQL service.")
        elif err.errno == 1045:
            print("   -> Access Denied: Incorrect username or password. Check config.py.")
        elif err.errno == 1049:
            print("   -> Database 'data_redundancy_db' does not exist. Please run schema.sql.")
        else:
            print(f"   -> {err}")

if __name__ == "__main__":
    test_connection()
