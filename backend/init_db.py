import sqlite3
import os

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "models", "schema.sql")

def get_db_path(custom_path=None):
    """
    Resolve the SQLite database path.
    Priority:
    1. Explicit custom_path argument
    2. DATABASE_PATH environment variable (for Render Persistent Disk, e.g. /data/grain_guardian.db)
    3. Default local path (backend/grain_guardian.db)
    """
    if custom_path:
        return os.path.abspath(custom_path)
    env_path = os.environ.get("DATABASE_PATH")
    if env_path:
        return os.path.abspath(env_path)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "grain_guardian.db"))

DB_PATH = get_db_path()

def init_db(db_path=None):
    """
    Initialize SQLite database tables from schema.sql.
    Safe to run repeatedly (uses CREATE TABLE IF NOT EXISTS and checks migrations).
    """
    target_path = get_db_path(db_path)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    conn = sqlite3.connect(target_path, timeout=30.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    cursor = conn.cursor()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    cursor.executescript(schema_sql)
    
    # Migrations for existing databases: ensure scan_results columns exist
    cursor.execute("PRAGMA table_info(scan_results)")
    existing_scan_cols = [row[1] for row in cursor.fetchall()]
    if "mask_path" not in existing_scan_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN mask_path TEXT")
    if "fluorescence_area_pct" not in existing_scan_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN fluorescence_area_pct REAL DEFAULT 0.0")
    if "screening_status" not in existing_scan_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN screening_status TEXT DEFAULT 'Clear'")
    if "sound_kernels_pct" not in existing_scan_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN sound_kernels_pct REAL DEFAULT 95.0")
    if "mold_defect_pct" not in existing_scan_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN mold_defect_pct REAL DEFAULT 0.0")
    if "broken_pct" not in existing_scan_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN broken_pct REAL DEFAULT 0.0")
    if "kernel_count" not in existing_scan_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN kernel_count INTEGER DEFAULT 0")
    if "seed_grade" not in existing_scan_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN seed_grade TEXT DEFAULT 'Grade A (Premium Grade)'")
    if "recommendation" not in existing_scan_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN recommendation TEXT DEFAULT ''")
    if "details_json" not in existing_scan_cols:
        cursor.execute("ALTER TABLE scan_results ADD COLUMN details_json TEXT DEFAULT '{}'")

    # Migrations for sensor_readings: raw_moisture and mq2_raw
    cursor.execute("PRAGMA table_info(sensor_readings)")
    existing_sensor_cols = [row[1] for row in cursor.fetchall()]
    if "raw_moisture" not in existing_sensor_cols:
        cursor.execute("ALTER TABLE sensor_readings ADD COLUMN raw_moisture INTEGER")
    if "mq2_raw" not in existing_sensor_cols:
        cursor.execute("ALTER TABLE sensor_readings ADD COLUMN mq2_raw INTEGER")

    conn.commit()
    conn.close()
    return target_path

if __name__ == "__main__":
    path = init_db()
    print(f"Database schema successfully initialized/verified at: {path}")
