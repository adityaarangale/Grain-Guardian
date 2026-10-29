# Grain Guardian

> **AI-Powered Post-Harvest Grain Storage Monitoring & Early Spoilage Detection System**

Grain Guardian provides real-time environmental monitoring, agronomic AI spoilage risk prediction, 365nm UV optical aflatoxin screening, and automated threshold breach alerts for grain silos, bins, and warehouses (Wheat, Maize, Groundnut, Rice, Pulses).

---

## 1. Hardware Architecture & Sensor Contract

The monitoring node utilizes dedicated precision sensors:
- **DHT22**: Temperature (°C) and Ambient Relative Humidity (% RH)
- **MQ-135**: Gas Index (baseline-relative continuous indoor air and respiration index)
- **Capacitive Moisture Probe V1.2**: Grain moisture content (%)
- **365nm UV Chamber**: Bright Greenish-Yellow Fluorescence (BGYF) optical contamination screening

### Final Sensor Contract (JSON)
All telemetry sent from the hardware bridge or ESP32 adheres to this contract:
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

---

## 2. Connect Hardware in 5 Steps

When real parts arrive, connect physical hardware to Grain Guardian seamlessly without changing backend or frontend code:

### Step 1: Find COM Port
- Connect your Arduino Uno / ESP32 to your computer via USB.
- **Windows**: Open **Device Manager** &rarr; expand **Ports (COM & LPT)** &rarr; identify your port (e.g. `COM3`, `COM4`, `COM5`).
- **Linux / macOS**: Open terminal and run `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`.

### Step 2: Set `.env` Configuration
- Open or create `.env` in the repository root (or copy from `.env.example`):
  ```ini
  # Hardware Bridge Configuration
  SERIAL_PORT=COM3          # Set to your identified serial port
  BAUD=9600                 # Standard baud rate
  API_URL=http://localhost:5000
  SIMULATE=0                # Set to 0 for physical hardware mode!
  ```

### Step 3: Upload Sketch
- Wire the sensors:
  - **DHT22**: Digital Pin 4
  - **MQ-135**: Analog Pin A0 (Clean-air baseline calibrated)
  - **Capacitive Moisture Probe V1.2**: Analog Pin A1
- Open the project in Arduino IDE or PlatformIO (`embedded/platformio.ini`) and upload the sketch to the board.
- The Arduino will stream newline-delimited JSON telemetry at 9600 baud.

### Step 4: Run Backend
- Start the Flask REST API server:
  ```bash
  python backend/app.py
  ```
  Backend will run on `http://localhost:5000`.

### Step 5: Run Bridge
- Start the hardware bridge daemon:
  ```bash
  python hardware_bridge.py
  ```
- The bridge reads incoming serial lines, parses telemetry against the contract, and posts directly to `/api/sensor-data`.

---

## 3. REST API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health check, database status, and `simulate` mode flag |
| `GET` | `/api/storage-units` | List registered storage silos and bins (optional `?grain_type=`) |
| `POST` | `/api/sensor-data` | Telemetry ingestion endpoint (stores reading and checks alerts) |
| `GET` | `/api/dashboard/<id>` | Full dashboard report (latest reading, prediction, scan, thresholds) |
| `GET` | `/api/readings?unit=&range=` | Historical sensor readings filtered by unit and range (`24h`, `7d`, `30d`) |
| `GET` | `/api/alerts` | Anomaly alerts (supports `?alert_type=&severity=&acknowledged=`) |
| `POST` | `/api/alerts/<id>/acknowledge` | Mark an alert as acknowledged |
| `POST` | `/api/scan-request` | Initiate automated UV screening job (polls through steps to Done) |
| `GET` | `/api/scans` | List historical UV contamination scans |
| `POST` | `/api/calibrate-baseline` | Store or recalibrate MQ-135 clean-air baseline |

---

## 4. Frontend Application

The frontend consists of 6 unified pages sharing one layout, design token system, and synchronized state:
1. **Dashboard** (`frontend/pages/dashboard.html`): Key KPIs, live reading strip, active units table, latest alerts, and last scan.
2. **Storage Monitoring** (`frontend/pages/storage-monitoring.html`): 4 live sensor metric cards, system status with clean-air baseline calibration, and sensor log table.
3. **AI Prediction** (`frontend/pages/ai-prediction.html`): Spoilage probability donut, safe storage range, 14-day risk trajectory, and input factor breakdown.
4. **Contamination Scan** (`frontend/pages/contamination-scan.html`): Interactive UV scan stepper, real 365nm optical frame, HSV fluorescence overlay mask, and recent scans.
5. **Analytics** (`frontend/pages/analytics.html`): 4 telemetry curve line charts (Temp, Humidity, Gas Index, Moisture), overall risk chart, and CSV export.
6. **Alerts** (`frontend/pages/alerts.html`): Real filterable alert stream, "View Details" modal with exact sensor readings, and acknowledgment.

*Note: The frontend automatically displays a **"Demo data"** badge in the top bar only when the API reports simulation mode (`SIMULATE=1`).*

---

## 5. Development & Testing

Run all backend endpoints and auth integration tests:
```bash
python backend/test_api.py
```

Test AI prediction model standalone:
```bash
python ai-model/test_predict.py
```

Run hardware bridge in single-shot test mode:
```bash
python hardware_bridge.py --once
```
