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

---

## 4. Frontend Application Structure

The web application is structured at the project root for frictionless **Git Deployment** (GitHub Pages, Vercel, Netlify, or direct Flask serving):

- **Login / Entry Point** (`index.html`): Secure authentication interface with 1-click **Live Demo Mode** fallback for static hosting.
- **Sign Up** (`signup.html`): Operator registration.
- **Dashboard** (`pages/dashboard.html`): Facility KPI overview, live telemetry status strip, active units table, latest alerts, and UV scan preview.
- **Storage Monitoring** (`pages/storage-monitoring.html`): 4 real-time sensor cards (Temp, Humidity, Gas Index, Moisture), hardware calibration, and sensor reading history.
- **AI Prediction** (`pages/ai-prediction.html`): Agronomic spoilage probability gauge, safe storage days range, 14-day risk trajectory chart, and environmental factor breakdown.
- **Contamination Scan** (`pages/contamination-scan.html`): 365nm UV fluorescence screening stepper, real-time OpenCV HSV luminescence segmentation mask overlay, and historical screening log.
- **Analytics** (`pages/analytics.html`): Multi-sensor historical telemetry trend charts, interactive time range filter (24h, 7d, 30d), and CSV dataset export.
- **Alerts** (`pages/alerts.html`): Real-time threshold breach notifications with modal sensor inspection and acknowledgment workflow.

---

## 5. Git Deployment Guide

### Option A: GitHub Pages (Instant Static Frontend Demo)
1. Push your repository to GitHub.
2. In your GitHub repo, navigate to **Settings** &rarr; **Pages**.
3. Under **Build and deployment**:
   - **Source**: `Deploy from a branch`
   - **Branch**: `main`
   - **Folder**: `/ (root)`
4. Click **Save**. Your site will be published at `https://<username>.github.io/grain-guardian/` within seconds!
5. Visitors can log in against a live backend or click **"Explore Live Demo Mode"** to test all telemetry, AI charts, and UV optical filters offline.

### Option B: Full-Stack Cloud Deployment (Render / Railway / Heroku)
The repository includes a ready-to-use `Procfile` and root `requirements.txt`:
1. Connect your GitHub repository to **Render** (or Railway / Heroku).
2. Choose **Web Service** with **Python 3.11+** environment.
3. Build Command:
   ```bash
   pip install -r requirements.txt
   ```
4. Start Command:
   ```bash
   gunicorn --chdir backend app:app
   ```
   *(Or let the platform automatically read `Procfile`)*.
5. In your frontend or browser, set `window.GRAIN_GUARDIAN_API_URL` or `localStorage.setItem("gg_api_url", "https://your-service.onrender.com/api")`.

---

## 6. Local Development & Testing

### Running the System Locally
1. **Start Backend API & Web Server**:
   ```bash
   python backend/app.py
   ```
   *Serves both the REST API and the frontend at `http://localhost:5000`.*

2. **Start Hardware Bridge (or Simulator)**:
   ```bash
   python hardware_bridge.py
   ```

3. **Alternative Static Local Server**:
   ```bash
   python -m http.server 8000
   ```
   *Open `http://localhost:8000` in your web browser.*

### Running Automated Test Suites
- **Full Backend API & JWT Auth Tests**:
  ```bash
  python backend/test_api.py
  ```
- **AI Prediction & Contamination Model Standalone Tests**:
  ```bash
  python ai-model/test_predict.py
  ```
- **Hardware Bridge Ingestion Verification**:
  ```bash
  python hardware_bridge.py --once
  ```