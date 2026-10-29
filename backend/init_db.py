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
    conn.commit()
    conn.close()
    print("Database schema successfully created/verified!")

if __name__ == "__main__":
    init_db()
