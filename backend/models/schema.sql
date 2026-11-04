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
    raw_moisture INTEGER,
    mq2_raw INTEGER,
    FOREIGN KEY (storage_unit_id) REFERENCES storage_units (id)
);

-- 4. Device Commands Table (Separate from sensor telemetry)
CREATE TABLE IF NOT EXISTS device_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_id TEXT UNIQUE NOT NULL,
    action TEXT NOT NULL,
    payload TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    result TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    executed_at DATETIME
);

-- 5. Device Heartbeats Table
CREATE TABLE IF NOT EXISTS device_heartbeats (
    device_id TEXT PRIMARY KEY,
    device_type TEXT NOT NULL,
    ip_address TEXT,
    firmware_version TEXT,
    stream_url TEXT,
    status TEXT,
    last_heartbeat DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. Contamination Scan Results Table
CREATE TABLE IF NOT EXISTS scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    storage_unit_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT NOT NULL,
    mask_path TEXT,
    contamination_risk TEXT NOT NULL,
    confidence REAL NOT NULL,
    fluorescence_area_pct REAL DEFAULT 0.0,
    screening_status TEXT DEFAULT 'Clear',
    sound_kernels_pct REAL DEFAULT 95.0,
    mold_defect_pct REAL DEFAULT 0.0,
    broken_pct REAL DEFAULT 0.0,
    kernel_count INTEGER DEFAULT 0,
    seed_grade TEXT DEFAULT 'Grade A (Premium Grade)',
    recommendation TEXT DEFAULT '',
    details_json TEXT DEFAULT '{}',
    FOREIGN KEY (storage_unit_id) REFERENCES storage_units (id)
);

-- 7. AI Spoilage Predictions Table
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

-- 8. Alerts Table
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
