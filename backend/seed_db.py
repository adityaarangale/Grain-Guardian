import sqlite3
import os
import sys

# Ensure backend directory is in python module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from init_db import init_db, get_db_path

def seed_database(db_path=None):
    """
    Seeds initial reference data if tables are empty.
    Safe to run repeatedly on startup (never overwrites existing records).
    """
    target_path = get_db_path(db_path)
    init_db(target_path)

    conn = sqlite3.connect(target_path, timeout=30.0)
    cursor = conn.cursor()

    # 1. Seed default storage units if empty
    cursor.execute("SELECT COUNT(*) FROM storage_units")
    count_units = cursor.fetchone()[0]
    if count_units == 0:
        units = [
            ("Silo A - North Sector", "wheat"),
            ("Warehouse 2 - Bin 4", "maize"),
            ("Cooperative Depot - Store 1", "groundnut")
        ]
        cursor.executemany("INSERT INTO storage_units (location, grain_type) VALUES (?, ?)", units)
        conn.commit()
        print(f"[Seed] Successfully seeded {len(units)} default storage units.")
    else:
        print(f"[Seed] Database already contains {count_units} storage units. Skipping units seed.")

    # 2. Seed default manager user account if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    count_users = cursor.fetchone()[0]
    if count_users == 0:
        from flask_bcrypt import Bcrypt
        from flask import Flask
        _b = Bcrypt(Flask(__name__))
        default_hash = _b.generate_password_hash("Password123!").decode("utf-8")
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, 'manager')
        """, ("Warehouse Manager", "manager_test@facility.com", default_hash))
        conn.commit()
        print("[Seed] Successfully seeded default manager account (manager_test@facility.com).")
    else:
        print(f"[Seed] Database already contains {count_users} user account(s). Skipping user seed.")

    conn.close()
    return target_path

if __name__ == "__main__":
    path = seed_database()
    print(f"Database seed complete at: {path}")
