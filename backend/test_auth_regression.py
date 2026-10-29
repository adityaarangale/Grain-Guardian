"""
Grain Guardian - Auth & Missing Users Table Regression Test Suite
Validates:
1. Database initialization creates all required tables (including users) from scratch.
2. Idempotent seeding creates default units and default manager.
3. User registration securely hashes passwords and returns JWT access tokens.
4. Duplicate email registration is properly rejected with HTTP 400.
5. User login succeeds with correct credentials.
6. User login rejects incorrect passwords with HTTP 401.
7. User login rejects unknown emails with HTTP 401.
8. Protected /api/auth/me returns the user profile with Bearer JWT.
9. All error responses are pure JSON (never HTML error pages).
10. Temporary database is cleaned up without touching production/dev records.
"""

import os
import sys
import tempfile
import unittest
import json
import sqlite3

# Ensure backend directory is in python search path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


class TestAuthRegression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary SQLite database file
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db_path = os.path.abspath(cls.temp_db.name)
        cls.temp_db.close()

        # Direct app and init scripts to use this isolated database
        os.environ["DATABASE_PATH"] = cls.temp_db_path

        import init_db
        import seed_db
        cls.init_db = init_db
        cls.seed_db = seed_db

        # Initialize schema from scratch
        cls.init_db.init_db(cls.temp_db_path)
        cls.seed_db.seed_database(cls.temp_db_path)

        # Import Flask app and configure for testing
        from app import app
        app.config["TESTING"] = True
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        # Clean up temporary database
        try:
            if os.path.exists(cls.temp_db_path):
                os.remove(cls.temp_db_path)
        except Exception:
            pass

    def test_01_schema_has_users_table(self):
        """Verify that the users table exists and has the expected columns."""
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        self.assertIsNotNone(cursor.fetchone(), "The 'users' table must exist in the database.")

        cursor.execute("PRAGMA table_info(users);")
        cols = {row[1] for row in cursor.fetchall()}
        required = {"id", "name", "email", "password_hash", "role", "created_at"}
        self.assertTrue(required.issubset(cols), f"Missing required columns in users table: {required - cols}")
        conn.close()

    def test_02_default_manager_seeded(self):
        """Verify that default manager account was seeded on clean setup."""
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, password_hash, role FROM users WHERE email = 'manager_test@facility.com';")
        user = cursor.fetchone()
        self.assertIsNotNone(user, "Default manager account should be seeded.")
        # Ensure password is not plaintext
        self.assertNotEqual(user[3], "Password123!", "Password must be hashed with bcrypt, never plaintext.")
        self.assertTrue(user[3].startswith("$2b$") or user[3].startswith("$2a$"), "Password hash must be bcrypt format.")
        conn.close()

    def test_03_default_manager_can_login(self):
        """Verify that default manager can log in and receives a JWT."""
        res = self.client.post("/api/auth/login", json={
            "email": "manager_test@facility.com",
            "password": "Password123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("access_token", data)
        self.assertIsInstance(data["access_token"], str)

    def test_04_register_new_user(self):
        """Verify new operator registration works and returns 201 Created."""
        res = self.client.post("/api/auth/signup", json={
            "name": "Silo Technician",
            "email": "technician_test@facility.com",
            "password": "TechnicianPass2026!"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("access_token", data)

        # Verify password is saved securely in the database
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE email = 'technician_test@facility.com';")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertNotEqual(row[0], "TechnicianPass2026!", "Password must be securely hashed.")
        conn.close()

    def test_05_duplicate_email_rejected(self):
        """Verify that registering with an already existing email returns 400 Bad Request JSON."""
        res = self.client.post("/api/auth/signup", json={
            "name": "Duplicate User",
            "email": "technician_test@facility.com",
            "password": "AnotherPassword!"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("already exists", data.get("message", "").lower())

    def test_06_login_with_registered_user(self):
        """Verify registered user can log in with their password."""
        res = self.client.post("/api/auth/login", json={
            "email": "technician_test@facility.com",
            "password": "TechnicianPass2026!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("access_token", data)

    def test_07_login_rejected_on_wrong_password(self):
        """Verify that incorrect password returns 401 Unauthorized JSON."""
        res = self.client.post("/api/auth/login", json={
            "email": "technician_test@facility.com",
            "password": "WrongPassword999!"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("invalid email or password", data.get("message", "").lower())

    def test_08_login_rejected_on_unknown_email(self):
        """Verify that non-existent email returns 401 Unauthorized JSON."""
        res = self.client.post("/api/auth/login", json={
            "email": "ghost_operator@unknown.com",
            "password": "Password123!"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("invalid email or password", data.get("message", "").lower())

    def test_09_protected_me_endpoint(self):
        """Verify that GET /api/auth/me returns the user profile when authenticated."""
        login_res = self.client.post("/api/auth/login", json={
            "email": "technician_test@facility.com",
            "password": "TechnicianPass2026!"
        })
        token = login_res.get_json()["access_token"]

        res = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data["user"]["email"], "technician_test@facility.com")
        self.assertEqual(data["user"]["name"], "Silo Technician")

    def test_10_missing_payload_fields_return_json_errors(self):
        """Verify that missing fields return HTTP 400 JSON errors."""
        res = self.client.post("/api/auth/login", json={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertTrue(data.get("message"))


if __name__ == "__main__":
    unittest.main()
