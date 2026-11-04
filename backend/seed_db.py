import sqlite3
import os
import sys

# Ensure backend directory is in python module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from init_db import init_db, get_db_path

def seed_database(db_path=None):
    """
    Seeds initial reference data if tables are empty.
    Safe to run repeatedly on startup (never overwrites existing custom records).
    Guarantees default manager and test accounts are always accessible.
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

    # 2. Guarantee default accounts exist and are valid
    from flask_bcrypt import Bcrypt
    from flask import Flask
    _b = Bcrypt(Flask(__name__))
    default_hash = _b.generate_password_hash("Password123!").decode("utf-8")

    default_accounts = [
        ("Warehouse Manager", "manager_test@facility.com", default_hash, "manager"),
        ("System Administrator", "admin@facility.com", default_hash, "admin"),
        ("Grain Guardian Admin", "admin@grainguardian.com", default_hash, "admin"),
        ("Facility Operator", "operator@facility.com", default_hash, "operator"),
        ("Aditya Arangale", "aditya@grainguardian.com", default_hash, "manager"),
    ]

    for name, email, pw_hash, role in default_accounts:
        cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (name, email, pw_hash, role))
            print(f"[Seed] Seeded default account: {email}")
        elif email == "manager_test@facility.com":
            # Ensure the primary test account password matches Password123!
            try:
                if not _b.check_password_hash(row[1], "Password123!"):
                    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, row[0]))
                    print("[Seed] Refreshed default manager password hash.")
            except Exception:
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, row[0]))

    conn.commit()
    conn.close()
    return target_path

if __name__ == "__main__":
    path = seed_database()
    print(f"Database seed complete at: {path}")
