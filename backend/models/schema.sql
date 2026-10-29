-- SQLite Database Schema for Grain Guardian Backend

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'manager',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Storage Units Table
CREATE TABLE IF NOT EXISTS storage_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    grain_type TEXT NOT NULL
);

-- 3. Sensor Readings Table
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    storage_unit_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    gas_index INTEGER NOT NULL,
    moisture REAL NOT NULL,
    FOREIGN KEY (storage_unit_id) REFERENCES storage_units (id)
);

-- 4. Contamination Scan Results Table
CREATE TABLE IF NOT EXISTS scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    storage_unit_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT NOT NULL,
    contamination_risk TEXT NOT NULL,
    confidence REAL NOT NULL,
    FOREIGN KEY (storage_unit_id) REFERENCES storage_units (id)
);

-- 5. AI Spoilage Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    storage_unit_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    risk_level TEXT NOT NULL,
    spoilage_probability REAL NOT NULL,
    safe_days_remaining INTEGER NOT NULL,
    recommendation TEXT NOT NULL,
    FOREIGN KEY (storage_unit_id) REFERENCES storage_units (id)
);

-- 6. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    storage_unit_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    reading_values TEXT,
    acknowledged INTEGER DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (storage_unit_id) REFERENCES storage_units (id)
);

