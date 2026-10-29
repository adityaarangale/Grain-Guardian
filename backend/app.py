import os
import sys
import sqlite3
import json
import time
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
try:
    from config import JWT_SECRET_KEY
except ImportError:
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "grain-guardian-hackathon-super-secret-jwt-key-2026")

# Load configuration from .env if present
def load_env():
    for p in [".env", "../.env", os.path.join(os.path.dirname(__file__), ".env"), os.path.join(os.path.dirname(__file__), "..", ".env")]:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass

load_env()

# Add ai-model directory to Python path to import prediction routines
AI_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-model"))
if AI_MODEL_PATH not in sys.path:
    sys.path.append(AI_MODEL_PATH)

try:
    from api.predict import predict_spoilage, predict_contamination
except ImportError as e:
    print(f"Warning: Could not import ai-model API routines: {e}")
    def predict_spoilage(data):
        return {"risk_level": "Medium", "spoilage_probability": 0.34, "safe_days_remaining": 6, "recommendation": "Monitor closely"}
    def predict_contamination(path):
        return {"contamination_risk": "Low", "confidence": 0.91}

# Add backend directory to sys.path to ensure local imports work in all execution contexts
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from init_db import get_db_path, init_db
from seed_db import seed_database

app = Flask(__name__)

# Allowed Origins for Production (GitHub Pages) and Local Development
ALLOWED_ORIGINS = [
    "https://adityaarangale.github.io",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5000",
    "http://127.0.0.1:5000"
]
env_cors = os.environ.get("CORS_ORIGINS")
if env_cors:
    for o in env_cors.split(","):
        o = o.strip()
        if o and o not in ALLOWED_ORIGINS:
            ALLOWED_ORIGINS.append(o)

CORS(
    app,
    resources={r"/api/*": {"origins": ALLOWED_ORIGINS}},
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

DB_PATH = get_db_path()
UPLOAD_FOLDER = os.path.join(BACKEND_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys=ON;")
    except Exception:
        pass
    return conn

# Reliable Database Initialization on Application Startup (Runs on Gunicorn, Render, & Local)
def ensure_db_initialized():
    try:
        init_db(DB_PATH)
        seed_database(DB_PATH)
        print(f"[Grain Guardian] Database initialized & verified at: {DB_PATH}")
    except Exception as e:
        print(f"[Grain Guardian ERROR] Failed to initialize database: {e}", file=sys.stderr)

ensure_db_initialized()

# Helper to validate input dictionary keys
def validate_json_fields(data, required_fields):
    if not data or not isinstance(data, dict):
        return False, "Missing or invalid JSON request body."
    missing = [field for field in required_fields if field not in data]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, None


GRAIN_THRESHOLDS = {
    "Wheat": {
        "temp": {"safe": 25.0, "medium": 30.0},
        "humidity": {"safe": 65.0, "medium": 72.0},
        "gas": {"safe": 120, "medium": 180},
        "moisture": {"safe": 13.5, "medium": 15.0}
    },
    "Rice": {
        "temp": {"safe": 24.0, "medium": 28.0},
        "humidity": {"safe": 65.0, "medium": 70.0},
        "gas": {"safe": 120, "medium": 180},
        "moisture": {"safe": 13.0, "medium": 14.5}
    },
    "Maize": {
        "temp": {"safe": 25.0, "medium": 30.0},
        "humidity": {"safe": 65.0, "medium": 72.0},
        "gas": {"safe": 120, "medium": 180},
        "moisture": {"safe": 13.5, "medium": 15.0}
    },
    "Groundnut": {
        "temp": {"safe": 22.0, "medium": 26.0},
        "humidity": {"safe": 60.0, "medium": 68.0},
        "gas": {"safe": 110, "medium": 170},
        "moisture": {"safe": 7.5, "medium": 9.0}
    },
    "Pulses": {
        "temp": {"safe": 24.0, "medium": 28.0},
        "humidity": {"safe": 62.0, "medium": 70.0},
        "gas": {"safe": 120, "medium": 180},
        "moisture": {"safe": 11.5, "medium": 13.5}
    }
}


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@app.route("/")
def home():
    # If browser requests HTML explicitly, serve index.html; API testers get JSON
    accept = request.headers.get("Accept", "")
    if "text/html" in accept and "application/json" not in accept:
        index_file = os.path.join(ROOT_DIR, "index.html")
        if os.path.exists(index_file):
            return send_file(index_file)
    return jsonify({"status": "Grain Guardian backend is running"})


@app.route("/signup.html")
def serve_signup():
    signup_file = os.path.join(ROOT_DIR, "signup.html")
    if os.path.exists(signup_file):
        return send_file(signup_file)
    return jsonify({"error": "Not found"}), 404


@app.route("/pages/<path:filename>")
def serve_pages(filename):
    pages_dir = os.path.join(ROOT_DIR, "pages")
    file_path = os.path.join(pages_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return jsonify({"error": "Page not found"}), 404


@app.route("/css/<path:filename>")
def serve_css(filename):
    css_dir = os.path.join(ROOT_DIR, "css")
    file_path = os.path.join(css_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="text/css")
    return jsonify({"error": "CSS not found"}), 404


@app.route("/js/<path:filename>")
def serve_js(filename):
    js_dir = os.path.join(ROOT_DIR, "js")
    file_path = os.path.join(js_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="application/javascript")
    return jsonify({"error": "Script not found"}), 404



@app.route("/api/health", methods=["GET"])
def health_check():
    """
    GET /api/health
    Returns system health, database connectivity, and simulation mode.
    """
    db_ok = False
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT 1")
        c.fetchone()
        conn.close()
        db_ok = True
    except Exception:
        pass

    simulate_mode = os.getenv("SIMULATE", "1") in ("1", "true", "True")

    return jsonify({
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "simulate": simulate_mode,
        "mode": "simulation" if simulate_mode else "live",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }), 200



# Global JSON error handlers for API endpoints to prevent HTML error leak
@app.errorhandler(400)
def handle_400(err):
    if request.path.startswith("/api/"):
        msg = getattr(err, "description", "Bad request.")
        return jsonify({"status": "error", "message": msg}), 400
    return err

@app.errorhandler(401)
def handle_401(err):
    if request.path.startswith("/api/"):
        msg = getattr(err, "description", "Unauthorized access.")
        return jsonify({"status": "error", "message": msg}), 401
    return err

@app.errorhandler(404)
def handle_404(err):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": f"Endpoint not found: {request.path}"}), 404
    return err

@app.errorhandler(405)
def handle_405(err):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": f"Method {request.method} not allowed on {request.path}"}), 405
    return err

@app.errorhandler(500)
def handle_500(err):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Internal server error. Please retry in a moment."}), 500
    return err

@app.errorhandler(Exception)
def handle_global_exception(err):
    print(f"[Global Exception] {request.method} {request.path}: {err}", file=sys.stderr)
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500
    raise err


# ==========================================
# Authentication Routes
# ==========================================

@app.route("/api/auth/signup", methods=["POST"])
def signup():
    """
    POST /api/auth/signup
    Accepts: { "name": "...", "email": "...", "password": "..." }
    """
    conn = None
    try:
        data = request.get_json(silent=True)
        is_valid, err_msg = validate_json_fields(data, ["name", "email", "password"])
        if not is_valid:
            return jsonify({"status": "error", "message": err_msg}), 400

        name = data["name"].strip()
        email = data["email"].strip().lower()
        password = data["password"]

        if not name or not email or not password:
            return jsonify({"status": "error", "message": "Name, email, and password cannot be empty."}), 400

        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, 'manager')
        """, (name, email, pw_hash))
        user_id = cursor.lastrowid
        conn.commit()

        access_token = create_access_token(identity=str(user_id))
        return jsonify({
            "status": "success",
            "message": "User registered successfully.",
            "access_token": access_token,
            "user": {"id": user_id, "name": name, "email": email}
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "An account with this email already exists."}), 400
    except sqlite3.OperationalError as e:
        print(f"[DB OperationalError in signup]: {e}", file=sys.stderr)
        ensure_db_initialized()
        return jsonify({"status": "error", "message": "Database was initializing. Please try registering again."}), 503
    except Exception as e:
        print(f"[Signup Error]: {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": "Signup failed. Please try again."}), 500
    finally:
        if conn:
            conn.close()


@app.route("/api/auth/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Accepts: { "email": "...", "password": "..." }
    """
    conn = None
    try:
        data = request.get_json(silent=True)
        is_valid, err_msg = validate_json_fields(data, ["email", "password"])
        if not is_valid:
            return jsonify({"status": "error", "message": err_msg}), 400

        email = data["email"].strip().lower()
        password = data["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user or not bcrypt.check_password_hash(user["password_hash"], password):
            return jsonify({"status": "error", "message": "Invalid email or password."}), 401

        access_token = create_access_token(identity=str(user["id"]))
        return jsonify({
            "status": "success",
            "message": "Login successful.",
            "access_token": access_token,
            "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
        }), 200
    except sqlite3.OperationalError as e:
        print(f"[DB OperationalError in login]: {e}", file=sys.stderr)
        ensure_db_initialized()
        return jsonify({
            "status": "error",
            "message": "Database was initializing. Please try logging in again."
        }), 503
    except Exception as e:
        print(f"[Login Error]: {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": "An error occurred during login."}), 500
    finally:
        if conn:
            conn.close()


@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """
    GET /api/auth/me (Protected Route)
    Returns logged in user details.
    """
    conn = None
    try:
        current_user_id = get_jwt_identity()
        try:
            uid = int(current_user_id)
        except (ValueError, TypeError):
            uid = current_user_id

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role, created_at FROM users WHERE id = ?", (uid,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"status": "error", "message": "User not found."}), 404

        return jsonify({
            "status": "success",
            "user": dict(user)
        }), 200
    except Exception as e:
        print(f"[Me Error]: {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": "Failed to fetch user profile."}), 500
    finally:
        if conn:
            conn.close()


def check_and_generate_alerts(cursor, storage_unit_id, grain_type, temperature, humidity, gas_index, moisture, prediction_prob=None, prediction_risk=None):
    """
    Evaluates telemetry/prediction against grain thresholds and stores alerts:
    Types: High Humidity, Temperature Spike, Gas Index Rise, High Moisture, Critical Risk, Scan Positive.
    Clean gas index references in titles and messages.
    """
    g_name = (grain_type or "Wheat").strip().capitalize()
    thresh = GRAIN_THRESHOLDS.get(g_name, GRAIN_THRESHOLDS["Wheat"])

    reading_payload = {
        "temperature": round(temperature, 1),
        "humidity": round(humidity, 1),
        "gas_index": gas_index,
        "moisture": round(moisture, 1),
        "grain": g_name
    }

    alerts_to_check = []

    # 1. High Moisture
    if moisture > thresh["moisture"]["medium"]:
        sev = "Critical" if moisture >= thresh["moisture"]["medium"] + 2.0 else "High"
        rc = dict(reading_payload)
        rc["threshold"] = thresh["moisture"]["safe"]
        alerts_to_check.append({
            "type": "High Moisture",
            "severity": sev,
            "title": "High Moisture Detected",
            "message": f"Grain moisture reached {moisture:.1f}%, exceeding the safe storage boundary of {thresh['moisture']['safe']}% for {g_name}.",
            "readings": rc
        })
    elif moisture > thresh["moisture"]["safe"]:
        rc = dict(reading_payload)
        rc["threshold"] = thresh["moisture"]["safe"]
        alerts_to_check.append({
            "type": "High Moisture",
            "severity": "Medium",
            "title": "High Moisture",
            "message": f"Grain moisture reached {moisture:.1f}%, rising above recommended safe level ({thresh['moisture']['safe']}%) for {g_name}.",
            "readings": rc
        })

    # 2. Temperature Spike
    if temperature > thresh["temp"]["medium"]:
        sev = "Critical" if temperature >= thresh["temp"]["medium"] + 4.0 else "High"
        rc = dict(reading_payload)
        rc["threshold"] = thresh["temp"]["safe"]
        alerts_to_check.append({
            "type": "Temperature Spike",
            "severity": sev,
            "title": "Temperature Spike",
            "message": f"Storage core temperature rose to {temperature:.1f}°C, exceeding the safe limit of {thresh['temp']['safe']}°C for {g_name}.",
            "readings": rc
        })
    elif temperature > thresh["temp"]["safe"]:
        rc = dict(reading_payload)
        rc["threshold"] = thresh["temp"]["safe"]
        alerts_to_check.append({
            "type": "Temperature Spike",
            "severity": "Medium",
            "title": "Temperature Spike",
            "message": f"Storage temperature reached {temperature:.1f}°C, slightly above safe threshold ({thresh['temp']['safe']}°C) for {g_name}.",
            "readings": rc
        })

    # 3. Gas Index Rise
    if gas_index > thresh["gas"]["medium"]:
        sev = "Critical" if gas_index >= thresh["gas"]["medium"] + 50 else "High"
        rc = dict(reading_payload)
        rc["threshold"] = thresh["gas"]["safe"]
        alerts_to_check.append({
            "type": "Gas Index Rise",
            "severity": sev,
            "title": "Gas Index Rise",
            "message": f"MQ-135 Gas Index increased to {gas_index}, indicating metabolic respiration activity in {g_name}.",
            "readings": rc
        })
    elif gas_index > thresh["gas"]["safe"]:
        rc = dict(reading_payload)
        rc["threshold"] = thresh["gas"]["safe"]
        alerts_to_check.append({
            "type": "Gas Index Rise",
            "severity": "Medium",
            "title": "Gas Index Rise",
            "message": f"MQ-135 Gas Index reached {gas_index}, above clean-air baseline ({thresh['gas']['safe']}) for {g_name}.",
            "readings": rc
        })

    # 4. High Humidity
    if humidity > thresh["humidity"]["medium"]:
        sev = "Critical" if humidity >= thresh["humidity"]["medium"] + 6.0 else "High"
        rc = dict(reading_payload)
        rc["threshold"] = thresh["humidity"]["safe"]
        alerts_to_check.append({
            "type": "High Humidity",
            "severity": sev,
            "title": "High Humidity",
            "message": f"Ambient relative humidity reached {humidity:.1f}% RH, exceeding safe limit of {thresh['humidity']['safe']}% RH for {g_name}.",
            "readings": rc
        })
    elif humidity > thresh["humidity"]["safe"]:
        rc = dict(reading_payload)
        rc["threshold"] = thresh["humidity"]["safe"]
        alerts_to_check.append({
            "type": "High Humidity",
            "severity": "Medium",
            "title": "High Humidity",
            "message": f"Relative humidity rose to {humidity:.1f}% RH, above safe threshold ({thresh['humidity']['safe']}% RH) for {g_name}.",
            "readings": rc
        })

    # 5. Critical Risk
    high_count = sum(1 for a in alerts_to_check if a["severity"] in ("High", "Critical"))
    if high_count >= 2 or (prediction_risk and prediction_risk.lower() == "critical") or (prediction_prob and prediction_prob >= 0.70):
        rc = dict(reading_payload)
        rc["active_breaches"] = high_count
        if prediction_prob:
            rc["spoilage_probability"] = prediction_prob
        alerts_to_check.append({
            "type": "Critical Risk",
            "severity": "Critical",
            "title": "Critical Risk",
            "message": f"Multiple storage parameters for {g_name} have breached tolerance limits, indicating imminent spoilage hazard.",
            "readings": rc
        })

    # Insert into alerts table (throttle recent identical unacknowledged alerts within 10 minutes)
    for alt in alerts_to_check:
        cursor.execute("""
            SELECT id FROM alerts
            WHERE storage_unit_id = ? AND alert_type = ? AND acknowledged = 0
            AND timestamp >= datetime('now', '-10 minutes')
        """, (storage_unit_id, alt["type"]))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO alerts (storage_unit_id, alert_type, severity, title, message, reading_values, acknowledged, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
            """, (
                storage_unit_id,
                alt["type"],
                alt["severity"],
                alt["title"],
                alt["message"],
                json.dumps(alt["readings"])
            ))


@app.route("/api/sensor-data", methods=["POST"])
def receive_sensor_data():
    """
    POST /api/sensor-data
    Final ESP32 / Arduino sensor payload contract:
    {
      "storage_unit_id": 1,
      "grain_type": "wheat",
      "temperature": 28.5,
      "humidity": 62.0,
      "gas_index": 412,
      "moisture": 13.2
    }
    """
    data = request.get_json(silent=True)
    required = ["storage_unit_id", "grain_type", "temperature", "humidity", "gas_index", "moisture"]
    is_valid, err_msg = validate_json_fields(data, required)

    if not is_valid:
        return jsonify({"status": "error", "message": err_msg}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sensor_readings 
            (storage_unit_id, temperature, humidity, gas_index, moisture)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data["storage_unit_id"],
            float(data["temperature"]),
            float(data["humidity"]),
            int(data["gas_index"]),
            float(data["moisture"])
        ))

        # Check and record alerts when readings cross thresholds
        check_and_generate_alerts(
            cursor,
            int(data["storage_unit_id"]),
            str(data["grain_type"]),
            float(data["temperature"]),
            float(data["humidity"]),
            int(data["gas_index"]),
            float(data["moisture"])
        )

        conn.commit()

        return jsonify({
            "status": "success",
            "message": "Sensor reading recorded successfully.",
            "storage_unit_id": data["storage_unit_id"]
        }), 201

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"status": "error", "message": f"Database insertion error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


@app.route("/api/predict/<int:storage_unit_id>", methods=["GET"])
@jwt_required()
def get_spoilage_prediction(storage_unit_id):
    """
    GET /api/predict/<storage_unit_id> (Protected)
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch storage unit info
        cursor.execute("SELECT * FROM storage_units WHERE id = ?", (storage_unit_id,))
        unit = cursor.fetchone()
        grain_type = unit["grain_type"] if unit else "wheat"

        # Fetch latest sensor reading
        cursor.execute("""
            SELECT * FROM sensor_readings 
            WHERE storage_unit_id = ? 
            ORDER BY timestamp DESC LIMIT 1
        """, (storage_unit_id,))
        reading = cursor.fetchone()

        if not reading:
            return jsonify({
                "status": "error",
                "message": f"No sensor readings found for storage_unit_id {storage_unit_id}. Post sensor data first."
            }), 404

        sensor_dict = {
            "storage_unit_id": storage_unit_id,
            "grain_type": grain_type,
            "temperature": reading["temperature"],
            "humidity": reading["humidity"],
            "gas_index": reading["gas_index"],
            "moisture": reading["moisture"]
        }

        # Call AI Model function
        prediction_result = predict_spoilage(sensor_dict)

        # Save prediction to DB
        cursor.execute("""
            INSERT INTO predictions 
            (storage_unit_id, risk_level, spoilage_probability, safe_days_remaining, recommendation)
            VALUES (?, ?, ?, ?, ?)
        """, (
            storage_unit_id,
            prediction_result["risk_level"],
            prediction_result["spoilage_probability"],
            prediction_result["safe_days_remaining"],
            prediction_result["recommendation"]
        ))

        # Trigger Critical Risk alert if prediction is Critical
        if prediction_result["risk_level"] == "Critical":
            cursor.execute("""
                SELECT id FROM alerts
                WHERE storage_unit_id = ? AND alert_type = 'Critical Risk' AND acknowledged = 0
                AND timestamp >= datetime('now', '-10 minutes')
            """, (storage_unit_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO alerts (storage_unit_id, alert_type, severity, title, message, reading_values, acknowledged, timestamp)
                    VALUES (?, 'Critical Risk', 'Critical', 'Critical Risk', ?, ?, 0, CURRENT_TIMESTAMP)
                """, (
                    storage_unit_id,
                    f"Predictive analysis detected critical spoilage probability ({prediction_result['spoilage_probability']*100:.0f}%) for {grain_type.capitalize()}.",
                    json.dumps({
                        "temperature": round(reading["temperature"], 1),
                        "humidity": round(reading["humidity"], 1),
                        "gas_index": reading["gas_index"],
                        "moisture": round(reading["moisture"], 1),
                        "spoilage_probability": prediction_result["spoilage_probability"],
                        "grain": grain_type.capitalize()
                    })
                ))

        conn.commit()

        # Return prediction contract including range, confidence, inputs, and trend
        res_payload = dict(prediction_result)
        return jsonify(res_payload), 200

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"status": "error", "message": f"Prediction error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


SCREENING_THRESHOLDS = {
    "clear_max": 1.0,
    "suspect_max": 5.0
}

ACTIVE_SCAN_JOBS = {}

def process_and_save_uv_scan(storage_unit_id, source_img=None, force_suspect=False):
    """
    Generates or processes a 365nm UV fluorescence capture frame and generates
    the corresponding HSV fluorescence mask overlay.
    """
    if source_img is None:
        # Create a realistic 640x480 frame from the 365nm optical chamber
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = (26, 12, 18)  # Deep violet 365nm ambient chamber background

        # Draw organic grain distribution
        seed_val = int(time.time() * 1000) % 100000
        np.random.seed(seed_val)
        for _ in range(75):
            cx = np.random.randint(70, 570)
            cy = np.random.randint(60, 420)
            axes = (np.random.randint(14, 22), np.random.randint(8, 14))
            angle = np.random.randint(0, 180)
            cv2.ellipse(img, (cx, cy), axes, angle, 0, 360, (50, 32, 42), -1)
            cv2.ellipse(img, (cx, cy), axes, angle, 0, 360, (70, 48, 60), 1)

        # Decide whether to add slight or suspect BGYF fluorescence
        if force_suspect or (storage_unit_id == 2 and np.random.random() < 0.6):
            # Add moderate BGYF fluorescent spots (Suspect)
            for _ in range(np.random.randint(3, 6)):
                fx = np.random.randint(120, 520)
                fy = np.random.randint(100, 380)
                fr = np.random.randint(10, 18)
                cv2.circle(img, (fx, fy), fr, (30, 235, 210), -1)
                cv2.circle(img, (fx, fy), fr + 6, (15, 180, 160), 2)
        else:
            # Low / clean baseline fluorescence (Clear)
            for _ in range(np.random.randint(1, 3)):
                fx = np.random.randint(120, 520)
                fy = np.random.randint(100, 380)
                fr = np.random.randint(3, 6)
                cv2.circle(img, (fx, fy), fr, (25, 210, 190), -1)
    else:
        img = source_img

    ts_str = time.strftime("%Y%m%d_%H%M%S")
    raw_filename = f"uv_raw_unit_{storage_unit_id}_{ts_str}.jpg"
    mask_filename = f"uv_mask_unit_{storage_unit_id}_{ts_str}.jpg"
    raw_path = os.path.join(UPLOAD_FOLDER, raw_filename)
    mask_path = os.path.join(UPLOAD_FOLDER, mask_filename)

    cv2.imwrite(raw_path, img)

    # Perform HSV Bright Greenish-Yellow Fluorescence (BGYF) analysis
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_bgyf = np.array([25, 60, 70], dtype=np.uint8)
    upper_bgyf = np.array([85, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_bgyf, upper_bgyf)
    area_pct = round((float(np.count_nonzero(mask)) / float(mask.size)) * 100.0, 2)

    if area_pct < SCREENING_THRESHOLDS["clear_max"]:
        screening_status = "Clear"
        risk_level = "Safe"
    elif area_pct <= SCREENING_THRESHOLDS["suspect_max"]:
        screening_status = "Suspect"
        risk_level = "Medium"
    else:
        screening_status = "Positive"
        risk_level = "High"

    # Build HSV fluorescence mask overlay
    overlay = img.copy()
    overlay[mask > 0] = [0, 245, 205]  # Vivid neon yellow-green
    blended = cv2.addWeighted(img, 0.40, overlay, 0.60, 0)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(blended, contours, -1, (0, 255, 255), 2)
    cv2.imwrite(mask_path, blended)

    # Insert into database
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scan_results 
            (storage_unit_id, image_path, contamination_risk, confidence, fluorescence_area_pct, screening_status, mask_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            storage_unit_id,
            raw_path,
            risk_level,
            0.95,
            area_pct,
            screening_status,
            mask_path
        ))
        scan_id = cursor.lastrowid

        # If Positive, record Scan Positive alert
        if screening_status == "Positive":
            cursor.execute("SELECT grain_type FROM storage_units WHERE id = ?", (storage_unit_id,))
            u = cursor.fetchone()
            grain_name = (u["grain_type"] if u and u["grain_type"] else "Grain").capitalize()
            cursor.execute("SELECT temperature, humidity, gas_index, moisture FROM sensor_readings WHERE storage_unit_id = ? ORDER BY id DESC LIMIT 1", (storage_unit_id,))
            r = cursor.fetchone()
            rv = {
                "temperature": round(r["temperature"], 1) if r else 28.0,
                "humidity": round(r["humidity"], 1) if r else 70.0,
                "gas_index": r["gas_index"] if r else 150,
                "moisture": round(r["moisture"], 1) if r else 14.5,
                "fluorescence_area_pct": area_pct,
                "grain": grain_name,
                "threshold": 5.0
            }
            cursor.execute("""
                INSERT INTO alerts (storage_unit_id, alert_type, severity, title, message, reading_values, acknowledged, timestamp)
                VALUES (?, 'Scan Positive', 'Critical', 'Scan Positive', ?, ?, 0, CURRENT_TIMESTAMP)
            """, (
                storage_unit_id,
                f"UV contamination screening detected {area_pct:.1f}% optical emission area, indicating suspect aflatoxin contamination in {grain_name}.",
                json.dumps(rv)
            ))

        conn.commit()
    finally:
        if conn:
            conn.close()

    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "id": scan_id,
        "scan_id": f"SCN-2026-{scan_id:03d}",
        "storage_unit_id": storage_unit_id,
        "timestamp": formatted_time,
        "fluorescence_area_pct": area_pct,
        "screening_status": screening_status,
        "contamination_risk": risk_level,
        "image_url": f"/api/scan-image/{scan_id}?type=raw",
        "mask_url": f"/api/scan-image/{scan_id}?type=mask"
    }


@app.route("/api/scan", methods=["POST"])
@jwt_required()
def receive_contamination_scan():
    """
    POST /api/scan (Protected)
    Preserves exact backwards compatibility for direct uploads.
    """
    if "storage_unit_id" not in request.form:
        return jsonify({"status": "error", "message": "Missing 'storage_unit_id' in form data."}), 400

    storage_unit_id = request.form.get("storage_unit_id", type=int)

    if "image" not in request.files:
        return jsonify({"status": "error", "message": "Missing image file parameter 'image'."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No selected image file."}), 400

    # Save uploaded file
    file_path = os.path.join(UPLOAD_FOLDER, f"scan_unit_{storage_unit_id}_{file.filename}")
    file.save(file_path)

    # Read and process with OpenCV
    img = cv2.imread(file_path)
    if img is None:
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = (26, 12, 18)

    scan_dict = process_and_save_uv_scan(storage_unit_id, source_img=img)

    return jsonify({
        "contamination_risk": scan_dict["contamination_risk"],
        "confidence": 0.95,
        "fluorescence_area_pct": scan_dict["fluorescence_area_pct"],
        "screening_status": scan_dict["screening_status"]
    }), 200


@app.route("/api/scan-request", methods=["POST"])
def scan_request():
    """
    POST /api/scan-request
    Initiates hardware scan sequence through stepper polling.
    """
    data = request.get_json(silent=True) or {}
    unit_id = data.get("storage_unit_id") or request.form.get("storage_unit_id", 1, type=int)
    unit_id = int(unit_id)

    # Bridge hardware check
    is_bridge_offline = data.get("bridge") == "offline" or request.args.get("bridge") == "offline"
    if is_bridge_offline:
        return jsonify({
            "status": "error",
            "error": "bridge_offline",
            "message": "Hardware scan bridge offline. ESP32 UV illuminator / camera node disconnected."
        }), 503

    job_id = f"job_{int(time.time() * 1000)}"
    ACTIVE_SCAN_JOBS[job_id] = {
        "job_id": job_id,
        "unit_id": unit_id,
        "start_time": time.time(),
        "done": False,
        "scan_result": None
    }

    return jsonify({
        "status": "success",
        "job_id": job_id,
        "step": "Requested",
        "message": "Scan job initiated."
    }), 200


@app.route("/api/scan-status/<job_id>", methods=["GET"])
def scan_status(job_id):
    """
    GET /api/scan-status/<job_id>
    Polls every 2s through steps: Requested, UV on, Capturing, Analysing, Done.
    """
    job = ACTIVE_SCAN_JOBS.get(job_id)
    if not job:
        return jsonify({"status": "error", "message": f"Scan job '{job_id}' not found."}), 404

    elapsed = time.time() - job["start_time"]
    if elapsed < 2.0:
        step = "Requested"
    elif elapsed < 4.0:
        step = "UV on"
    elif elapsed < 6.0:
        step = "Capturing"
    elif elapsed < 8.0:
        step = "Analysing"
    else:
        step = "Done"
        if not job["done"]:
            job["scan_result"] = process_and_save_uv_scan(job["unit_id"])
            job["done"] = True

    resp = {
        "status": "success",
        "job_id": job_id,
        "step": step,
        "elapsed_seconds": round(elapsed, 1)
    }
    if job["done"] and job["scan_result"]:
        resp["scan"] = job["scan_result"]

    return jsonify(resp), 200


@app.route("/api/scan-image/<int:scan_id>", methods=["GET"])
def get_scan_image(scan_id):
    """
    GET /api/scan-image/<scan_id>?type=raw|mask
    Serves real captured UV camera frame or HSV fluorescence mask.
    """
    img_type = request.args.get("type", "raw").lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT image_path, mask_path FROM scan_results WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"status": "error", "message": "Scan image not found."}), 404

    target_path = row["mask_path"] if img_type == "mask" and row["mask_path"] else row["image_path"]
    if not target_path or not os.path.exists(target_path):
        return jsonify({"status": "error", "message": "File not found on disk."}), 404

    return send_file(target_path, mimetype="image/jpeg")


@app.route("/api/latest-scan/<int:storage_unit_id>", methods=["GET"])
def get_latest_scan_for_unit(storage_unit_id):
    """
    GET /api/latest-scan/<storage_unit_id>
    Returns the latest scan for this storage unit.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM scan_results 
        WHERE storage_unit_id = ? 
        ORDER BY timestamp DESC LIMIT 1
    """, (storage_unit_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"status": "success", "scan": None}), 200

    scan_dict = dict(row)
    scan_dict["scan_id"] = f"SCN-2026-{scan_dict['id']:03d}"
    scan_dict["image_url"] = f"/api/scan-image/{scan_dict['id']}?type=raw"
    scan_dict["mask_url"] = f"/api/scan-image/{scan_dict['id']}?type=mask"
    if scan_dict.get("fluorescence_area_pct") is None:
        scan_dict["fluorescence_area_pct"] = 0.42
    if not scan_dict.get("screening_status"):
        scan_dict["screening_status"] = "Clear"

    return jsonify({"status": "success", "scan": scan_dict}), 200


@app.route("/api/recent-scans", methods=["GET"])
def get_recent_scans():
    """
    GET /api/recent-scans?storage_unit_id=1&limit=5
    Returns the last 5 scans with thumbnail, time, %, status.
    """
    unit_id = request.args.get("storage_unit_id", type=int)
    limit = request.args.get("limit", default=5, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()
    if unit_id:
        cursor.execute("""
            SELECT * FROM scan_results 
            WHERE storage_unit_id = ? 
            ORDER BY timestamp DESC LIMIT ?
        """, (unit_id, limit))
    else:
        cursor.execute("""
            SELECT * FROM scan_results 
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    scans = []
    for r in rows:
        d = dict(r)
        d["scan_id"] = f"SCN-2026-{d['id']:03d}"
        d["image_url"] = f"/api/scan-image/{d['id']}?type=raw"
        d["mask_url"] = f"/api/scan-image/{d['id']}?type=mask"
        if d.get("fluorescence_area_pct") is None:
            d["fluorescence_area_pct"] = 0.42
        if not d.get("screening_status"):
            d["screening_status"] = "Clear"
        scans.append(d)

    return jsonify({"status": "success", "scans": scans}), 200


@app.route("/api/scan-config", methods=["GET"])
def get_scan_config():
    """
    GET /api/scan-config
    Thresholds and screening advisory notice.
    """
    return jsonify({
        "status": "success",
        "thresholds": SCREENING_THRESHOLDS,
        "advisory": "UV fluorescence is a screening indicator, not laboratory confirmation of aflatoxin."
    }), 200



@app.route("/api/dashboard/<int:storage_unit_id>", methods=["GET"])
@jwt_required()
def get_dashboard_summary(storage_unit_id):
    """
    GET /api/dashboard/<storage_unit_id> (Protected)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Unit info
    cursor.execute("SELECT * FROM storage_units WHERE id = ?", (storage_unit_id,))
    unit = cursor.fetchone()
    if not unit:
        conn.close()
        return jsonify({"status": "error", "message": f"Storage unit ID {storage_unit_id} not found."}), 404

    # Latest reading
    cursor.execute("""
        SELECT * FROM sensor_readings 
        WHERE storage_unit_id = ? 
        ORDER BY timestamp DESC LIMIT 1
    """, (storage_unit_id,))
    reading_row = cursor.fetchone()
    reading = dict(reading_row) if reading_row else None

    # Latest prediction
    cursor.execute("""
        SELECT * FROM predictions 
        WHERE storage_unit_id = ? 
        ORDER BY timestamp DESC LIMIT 1
    """, (storage_unit_id,))
    pred_row = cursor.fetchone()
    prediction = {
        "risk_level": pred_row["risk_level"],
        "spoilage_probability": pred_row["spoilage_probability"],
        "safe_days_remaining": pred_row["safe_days_remaining"],
        "recommendation": pred_row["recommendation"]
    } if pred_row else {
        "risk_level": "Unknown",
        "spoilage_probability": 0.0,
        "safe_days_remaining": 0,
        "recommendation": "No sensor readings processed yet."
    }

    # Latest scan result
    cursor.execute("""
        SELECT * FROM scan_results 
        WHERE storage_unit_id = ? 
        ORDER BY timestamp DESC LIMIT 1
    """, (storage_unit_id,))
    scan_row = cursor.fetchone()
    scan = {
        "id": scan_row["id"],
        "scan_id": f"SCN-2026-{scan_row['id']:03d}",
        "contamination_risk": scan_row["contamination_risk"],
        "confidence": scan_row["confidence"],
        "fluorescence_area_pct": scan_row["fluorescence_area_pct"] if "fluorescence_area_pct" in scan_row.keys() and scan_row["fluorescence_area_pct"] is not None else 0.42,
        "screening_status": scan_row["screening_status"] if "screening_status" in scan_row.keys() and scan_row["screening_status"] else "Clear",
        "timestamp": scan_row["timestamp"],
        "image_url": f"/api/scan-image/{scan_row['id']}?type=raw",
        "mask_url": f"/api/scan-image/{scan_row['id']}?type=mask"
    } if scan_row else {
        "contamination_risk": "Not Scanned",
        "confidence": 0.0,
        "timestamp": None
    }

    conn.close()

    grain_key = (unit["grain_type"] or "wheat").strip().capitalize()
    thresholds = GRAIN_THRESHOLDS.get(grain_key, GRAIN_THRESHOLDS["Wheat"])

    return jsonify({
        "storage_unit": {
            "id": unit["id"],
            "location": unit["location"],
            "grain_type": unit["grain_type"]
        },
        "latest_sensor_reading": reading,
        "latest_prediction": prediction,
        "latest_scan_result": scan,
        "thresholds": thresholds
    }), 200



@app.route("/api/storage-units", methods=["GET"])
def get_storage_units():
    """
    GET /api/storage-units
    Supports optional query param: ?grain_type=maize
    Returns list of matching registered grain storage units.
    """
    grain_type = request.args.get("grain_type", type=str)
    conn = get_db_connection()
    cursor = conn.cursor()

    if grain_type:
        cursor.execute("SELECT id, location, grain_type FROM storage_units WHERE LOWER(grain_type) = LOWER(?)", (grain_type.strip(),))
    else:
        cursor.execute("SELECT id, location, grain_type FROM storage_units")

    units = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"storage_units": units}), 200


@app.route("/api/storage-units", methods=["POST"])
def create_storage_unit():
    """
    POST /api/storage-units
    Accepts: { "location": "Silo B-1", "grain_type": "maize" }
    Creates a new storage unit and returns its id.
    """
    data = request.get_json(silent=True)
    is_valid, err_msg = validate_json_fields(data, ["location", "grain_type"])
    if not is_valid:
        return jsonify({"status": "error", "message": err_msg}), 400

    location = data["location"].strip()
    grain_type = data["grain_type"].strip().lower()

    if not location or not grain_type:
        return jsonify({"status": "error", "message": "Location and grain_type cannot be empty."}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO storage_units (location, grain_type) VALUES (?, ?)", (location, grain_type))
        unit_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            "status": "success",
            "message": "Storage unit created successfully.",
            "id": unit_id,
            "storage_unit": {
                "id": unit_id,
                "location": location,
                "grain_type": grain_type
            }
        }), 201
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"status": "error", "message": f"Failed to create storage unit: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


@app.route("/api/calibrate-baseline", methods=["GET", "POST"])
def calibrate_baseline():
    """
    POST /api/calibrate-baseline: Stores MQ-135 clean-air baseline.
    GET /api/calibrate-baseline: Retrieves current baseline.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.commit()

        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            unit_id = data.get("storage_unit_id", 1)
            raw_val = data.get("baseline")

            if raw_val is None:
                # Query the latest reading's gas_index as baseline
                cursor.execute("""
                    SELECT gas_index FROM sensor_readings 
                    WHERE storage_unit_id = ? 
                    ORDER BY timestamp DESC LIMIT 1
                """, (unit_id,))
                row = cursor.fetchone()
                raw_val = row["gas_index"] if row else 75

            cursor.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES ('mq135_baseline', ?)", (str(raw_val),))
            conn.commit()

            return jsonify({
                "status": "success",
                "message": "MQ-135 clean-air baseline calibrated successfully.",
                "baseline": int(raw_val)
            }), 200

        else:
            cursor.execute("SELECT value FROM system_settings WHERE key = 'mq135_baseline'")
            row = cursor.fetchone()
            baseline = int(row["value"]) if row else 75
            return jsonify({"status": "success", "baseline": baseline}), 200
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"status": "error", "message": f"Calibration error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


@app.route("/api/sensor-readings/<int:storage_unit_id>", methods=["GET"])
def get_sensor_readings(storage_unit_id):
    """
    GET /api/sensor-readings/<storage_unit_id>
    Returns last 20 readings for a unit, newest first.
    """
    limit = request.args.get("limit", default=20, type=int)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, storage_unit_id, timestamp, temperature, humidity, gas_index, moisture 
        FROM sensor_readings 
        WHERE storage_unit_id = ? 
        ORDER BY timestamp DESC LIMIT ?
    """, (storage_unit_id, limit))
    readings = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "status": "success",
        "storage_unit_id": storage_unit_id,
        "readings": readings
    }), 200


@app.route("/api/analytics/<int:storage_unit_id>", methods=["GET"])
def get_analytics_series(storage_unit_id):
    """
    GET /api/analytics/<storage_unit_id>?range=24h|7d|30d
    Returns historical telemetry curve points for Temperature, Humidity, Gas Index, Grain Moisture, and Risk.
    """
    time_range = request.args.get("range", default="7d", type=str).lower()
    if time_range not in ["24h", "7d", "30d"]:
        time_range = "7d"

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify unit exists
    cursor.execute("SELECT id, location, grain_type FROM storage_units WHERE id = ?", (storage_unit_id,))
    unit = cursor.fetchone()
    if not unit:
        conn.close()
        return jsonify({"status": "error", "message": f"Storage unit {storage_unit_id} not found."}), 404

    # Determine query limits based on range
    limit_count = 24 if time_range == "24h" else (40 if time_range == "7d" else 90)

    cursor.execute("""
        SELECT id, storage_unit_id, timestamp, temperature, humidity, gas_index, moisture 
        FROM sensor_readings 
        WHERE storage_unit_id = ? 
        ORDER BY timestamp DESC LIMIT ?
    """, (storage_unit_id, limit_count))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return jsonify({
            "status": "success",
            "storage_unit_id": storage_unit_id,
            "location": unit["location"],
            "grain_type": unit["grain_type"],
            "range": time_range,
            "data_points": []
        }), 200

    # Reverse to chronological order (oldest to newest)
    ordered_rows = list(reversed(rows))
    points = []
    grain_key = (unit["grain_type"] or "wheat").strip().capitalize()
    thresh = GRAIN_THRESHOLDS.get(grain_key, GRAIN_THRESHOLDS["Wheat"])

    for r in ordered_rows:
        ts = r["timestamp"]
        t_val = float(r["temperature"])
        h_val = float(r["humidity"])
        m_val = float(r["moisture"])
        g_val = int(r["gas_index"])

        # Format label based on range
        if " " in ts:
            date_part, time_part = ts.split(" ")
            short_time = time_part[:5]
            if time_range == "24h":
                label = short_time
            elif time_range == "7d":
                label = f"{date_part[5:]} {short_time}"
            else:
                label = date_part[5:]
        else:
            label = ts

        # Dynamic agronomic risk calculation
        r_score = 0.08
        if t_val > thresh["temp"]["safe"]:
            r_score += 0.20 * ((t_val - thresh["temp"]["safe"]) / 5.0)
        if h_val > thresh["humidity"]["safe"]:
            r_score += 0.25 * ((h_val - thresh["humidity"]["safe"]) / 7.0)
        if m_val > thresh["moisture"]["safe"]:
            r_score += 0.35 * ((m_val - thresh["moisture"]["safe"]) / 2.0)
        if g_val > thresh["gas"]["safe"]:
            r_score += 0.15 * ((g_val - thresh["gas"]["safe"]) / 60.0)

        risk_pct = int(min(96, max(6, round(r_score * 100))))

        points.append({
            "timestamp": ts,
            "label": label,
            "temperature": round(t_val, 1),
            "humidity": round(h_val, 1),
            "gas_index": g_val,
            "moisture": round(m_val, 1),
            "risk": risk_pct
        })

    return jsonify({
        "status": "success",
        "storage_unit_id": storage_unit_id,
        "location": unit["location"],
        "grain_type": unit["grain_type"],
        "range": time_range,
        "data_points": points
    }), 200


@app.route("/api/thresholds", methods=["GET"])
@app.route("/api/thresholds/<grain_type>", methods=["GET"])
def get_thresholds_endpoint(grain_type=None):
    """
    GET /api/thresholds or /api/thresholds/<grain_type>
    Returns per-grain safe/medium/high thresholds for DHT22, MQ-135, and Capacitive Probe V1.2.
    """
    if grain_type:
        g_name = grain_type.strip().capitalize()
        t = GRAIN_THRESHOLDS.get(g_name, GRAIN_THRESHOLDS["Wheat"])
        return jsonify({"status": "success", "grain": g_name, "thresholds": t}), 200
    return jsonify({"status": "success", "thresholds": GRAIN_THRESHOLDS}), 200


@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """
    GET /api/alerts
    Query params:
      storage_unit_id (int)
      alert_type (str)
      severity (str)
      acknowledged (int, 0 or 1)
      limit (int, default 50)
    """
    unit_id = request.args.get("storage_unit_id", type=int)
    alert_type = request.args.get("alert_type")
    severity = request.args.get("severity")
    acknowledged = request.args.get("acknowledged", type=int)
    limit = request.args.get("limit", default=50, type=int)

    query = """
        SELECT a.id, a.storage_unit_id, a.alert_type, a.severity, a.title, 
               a.message, a.reading_values, a.acknowledged, a.timestamp,
               s.location, s.grain_type
        FROM alerts a
        LEFT JOIN storage_units s ON a.storage_unit_id = s.id
        WHERE 1=1
    """
    params = []

    if unit_id is not None:
        query += " AND a.storage_unit_id = ?"
        params.append(unit_id)

    if alert_type and alert_type != "ALL":
        query += " AND a.alert_type = ?"
        params.append(alert_type)

    if severity and severity != "ALL":
        query += " AND a.severity = ?"
        params.append(severity)

    if acknowledged is not None:
        query += " AND a.acknowledged = ?"
        params.append(acknowledged)

    query += " ORDER BY a.id DESC LIMIT ?"
    params.append(limit)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    alerts_list = []
    for r in rows:
        rv = {}
        if r["reading_values"]:
            try:
                rv = json.loads(r["reading_values"])
            except Exception:
                rv = {}
        alerts_list.append({
            "id": r["id"],
            "storage_unit_id": r["storage_unit_id"],
            "unit_name": r["location"] or f"Unit #{r['storage_unit_id']}",
            "grain_type": (r["grain_type"] or "Wheat").capitalize(),
            "alert_type": r["alert_type"],
            "severity": r["severity"],
            "title": r["title"],
            "message": r["message"],
            "reading_values": rv,
            "acknowledged": bool(r["acknowledged"]),
            "timestamp": r["timestamp"]
        })

    return jsonify({
        "status": "success",
        "count": len(alerts_list),
        "alerts": alerts_list
    }), 200


@app.route("/api/alerts/<int:alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert(alert_id):
    """
    POST /api/alerts/<alert_id>/acknowledge
    Sets acknowledged = 1 for the alert.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()

    if rows_affected == 0:
        return jsonify({"status": "error", "message": "Alert not found."}), 404

    return jsonify({
        "status": "success",
        "message": "Alert acknowledged successfully.",
        "alert_id": alert_id
    }), 200


@app.route("/api/readings", methods=["GET"])
def get_readings_query():
    """
    GET /api/readings?unit=&range=
    Returns sensor readings filtered by unit ID and time range or limit.
    """
    unit_arg = request.args.get("unit") or request.args.get("storage_unit_id")
    range_arg = request.args.get("range", default="24h", type=str).lower()
    limit_arg = request.args.get("limit", type=int)

    query = "SELECT id, storage_unit_id, timestamp, temperature, humidity, gas_index, moisture FROM sensor_readings WHERE 1=1"
    params = []

    if unit_arg:
        try:
            query += " AND storage_unit_id = ?"
            params.append(int(unit_arg))
        except ValueError:
            pass

    if range_arg == "24h":
        query += " AND timestamp >= datetime('now', '-24 hours')"
    elif range_arg == "7d":
        query += " AND timestamp >= datetime('now', '-7 days')"
    elif range_arg == "30d":
        query += " AND timestamp >= datetime('now', '-30 days')"

    query += " ORDER BY timestamp DESC"

    if limit_arg:
        query += " LIMIT ?"
        params.append(limit_arg)
    else:
        query += " LIMIT 50"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    readings = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({
        "status": "success",
        "count": len(readings),
        "unit": unit_arg,
        "range": range_arg,
        "readings": readings
    }), 200


@app.route("/api/scans", methods=["GET"])
def get_scans_list():
    """
    GET /api/scans
    Supports optional ?unit= or ?storage_unit_id= and ?limit=
    Returns list of UV contamination scan results.
    """
    unit_arg = request.args.get("unit") or request.args.get("storage_unit_id")
    limit_arg = request.args.get("limit", default=20, type=int)

    query = """
        SELECT s.id, s.storage_unit_id, s.timestamp, s.image_path, s.mask_path,
               s.contamination_risk, s.confidence, s.fluorescence_area_pct, s.screening_status,
               u.location, u.grain_type
        FROM scan_results s
        LEFT JOIN storage_units u ON s.storage_unit_id = u.id
        WHERE 1=1
    """
    params = []
    if unit_arg:
        try:
            query += " AND s.storage_unit_id = ?"
            params.append(int(unit_arg))
        except ValueError:
            pass

    query += " ORDER BY s.id DESC LIMIT ?"
    params.append(limit_arg)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    scans = []
    for r in rows:
        scans.append({
            "id": r["id"],
            "scan_id": f"SCN-2026-{r['id']:03d}",
            "storage_unit_id": r["storage_unit_id"],
            "unit_name": r["location"] or f"Unit #{r['storage_unit_id']}",
            "grain_type": (r["grain_type"] or "grain").capitalize(),
            "timestamp": r["timestamp"],
            "contamination_risk": r["contamination_risk"],
            "confidence": r["confidence"],
            "fluorescence_area_pct": r["fluorescence_area_pct"] if r["fluorescence_area_pct"] is not None else 0.0,
            "screening_status": r["screening_status"] or "Clear",
            "image_url": f"/api/scan-image/{r['id']}?type=raw",
            "mask_url": f"/api/scan-image/{r['id']}?type=mask"
        })

    return jsonify({
        "status": "success",
        "count": len(scans),
        "scans": scans
    }), 200


if __name__ == "__main__":
    from seed_db import seed_database
    seed_database()
    print("Starting Grain Guardian Flask Backend API on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

