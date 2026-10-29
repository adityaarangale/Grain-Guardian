import sqlite3
import os
from init_db import init_db, DB_PATH

def seed_database():
    # Make sure DB and tables exist
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check existing units
    cursor.execute("SELECT COUNT(*) FROM storage_units")
    count = cursor.fetchone()[0]

    if count == 0:
        units = [
            ("Silo A - North Sector", "wheat"),
            ("Warehouse 2 - Bin 4", "maize"),
            ("Cooperative Depot - Store 1", "groundnut")
        ]
        cursor.executemany("INSERT INTO storage_units (location, grain_type) VALUES (?, ?)", units)
        conn.commit()
        print(f"Successfully seeded {len(units)} storage units (wheat, maize, groundnut).")
    else:
        print(f"Database already contains {count} storage units. Skipping seed.")

    conn.close()

if __name__ == "__main__":
    seed_database()
