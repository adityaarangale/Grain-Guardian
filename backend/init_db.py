import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "grain_guardian.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "models", "schema.sql")

def init_db():
    print(f"Initializing SQLite database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    cursor.executescript(schema_sql)
    
    # Check and add missing columns to scan_results if needed
    cursor.execute("PRAGMA table_info(scan_results)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    if "mask_path" not in existing_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN mask_path TEXT")
    if "fluorescence_area_pct" not in existing_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN fluorescence_area_pct REAL DEFAULT 0.0")
    if "screening_status" not in existing_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN screening_status TEXT DEFAULT 'Clear'")

    conn.commit()
    conn.close()
    print("Database schema successfully created/verified!")

if __name__ == "__main__":
    init_db()
