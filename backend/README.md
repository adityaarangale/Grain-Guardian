# Grain Guardian - Backend REST API Service

The backend layer is a **Flask + SQLite REST API** responsible for storing continuous IoT sensor telemetry, triggering AI spoilage predictions, receiving UV aflatoxin scan image uploads, and delivering aggregated dashboard metrics.

---

## 1. Directory Structure

```text
backend/
├── app.py                  # Core Flask REST application & endpoint routes
├── init_db.py              # Database initialization helper
├── seed_db.py              # Seeds default storage units (wheat, maize, groundnut)
├── test_api.py             # Integration test script using requests
├── requirements.txt        # Python dependency list
├── README.md               # Setup & execution documentation
├── models/
│   └── schema.sql          # SQLite table definitions
└── uploads/                # Directory for uploaded UV fluorescence scan images
```

---

## 2. Database Schema

The SQLite database (`grain_guardian.db`) contains 5 tables:
1. `users`: System users and roles.
2. `storage_units`: Registered storage facilities (wheat, maize, groundnut).
3. `sensor_readings`: Time-series IoT sensor data.
4. `scan_results`: UV-fluorescence scan image paths and aflatoxin predictions.
5. `predictions`: AI-generated spoilage risk scores, safe days remaining, and recommendations.

---

## 3. Fixed JSON Contracts & API Endpoints

### 1. Receive IoT Telemetry
- **POST** `/api/sensor-data`
- **Request Body**:
  ```json
  {
    "storage_unit_id": 1,
    "grain_type": "wheat",
    "temperature": 28.5,
    "humidity": 62.0,
    "gas_index": 412,
    "moisture": 13.2
  }
  ```

### 2. Spoilage Risk Prediction
- **GET** `/api/predict/<storage_unit_id>`
- **Response**:
  ```json
  {
    "risk_level": "Medium",
    "spoilage_probability": 0.34,
    "safe_days_remaining": 6,
    "recommendation": "Monitor closely, re-check in 3 days"
  }
  ```

### 3. Aflatoxin Contamination Scan
- **POST** `/api/scan` (Form data: `storage_unit_id` + `image` file)
- **Response**:
  ```json
  {
    "contamination_risk": "Low",
    "confidence": 0.91
  }
  ```

### 4. Combined Dashboard Report
- **GET** `/api/dashboard/<storage_unit_id>`
- Returns latest sensor reading, prediction, and contamination scan combined.

### 5. List Storage Units
- **GET** `/api/storage-units`
- Returns all registered storage units for UI dropdown selectors.

---

## 4. Setup & Running Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Seed Database
```bash
python seed_db.py
```

### 3. Launch Flask Backend Server
```bash
python app.py
```
The server will run on **`http://localhost:5000`** (or `http://<YOUR_IP>:5000`).

### 4. Verify API Endpoints (Standalone Test)
With `app.py` running in one terminal, run the automated tester in another terminal:
```bash
python test_api.py
```

---

## 5. Connect Hardware in 5 Steps

When real parts arrive, connect physical hardware to Grain Guardian seamlessly:

1. **Find COM Port**: Plug Arduino/ESP32 into USB. In Windows Device Manager, check **Ports (COM & LPT)** (e.g., `COM3`).
2. **Set `.env` Configuration**: Set `SERIAL_PORT=COM3`, `BAUD=9600`, `API_URL=http://localhost:5000`, and `SIMULATE=0`.
3. **Upload Sketch**: Flash the firmware to your board. Output streams JSON telemetry at 9600 baud.
4. **Run Backend**: Start `python backend/app.py` on `http://localhost:5000`.
5. **Run Bridge**: Start `python hardware_bridge.py`. Telemetry is forwarded to `/api/sensor-data` automatically!

