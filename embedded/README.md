# Grain Guardian - ESP32 Firmware Documentation

This directory contains the ESP32 IoT node firmware for the **Grain Guardian** project. The firmware reads atmospheric and grain condition sensors in real-time, packages the readings into JSON, posts data to the Flask backend, and controls a 365nm UV LED illumination array for aflatoxin scan triggering.

---

## 1. Hardware Pinout & Wiring Diagram Guide

| Sensor / Actuator | Parameter Measured | ESP32 Pin | Interface Type | Notes / Calibration Info |
| :--- | :--- | :--- | :--- | :--- |
| **DHT22** | Temperature & Humidity | `GPIO 4` | 1-Wire Digital | 10k pull-up resistor to 3.3V |
| **MQ-135** | Gas Index (Baseline-Relative) | `GPIO 34` | Analog (ADC1) | Clean air baseline calibration via `/api/calibrate-baseline` |
| **Capacitive Moisture Probe V1.2** | Grain Moisture (%) | `GPIO 35` | Analog (ADC1) | Uses `calibrateMoisture(rawValue)` in `sensors.cpp` |
| **UV LED Relay / MOSFET** | 365nm UV Light Actuator | `GPIO 25` | Digital Out | High = LEDs ON (5-second trigger) |
| **Physical Trigger Button** | Manual UV Scan Switch | `GPIO 13` | Digital In (Pullup) | Connect between GPIO 13 and GND |

---

## 2. Directory Structure

```text
embedded/
├── README.md                   # Wiring guide & setup instructions
├── wifi_config_template.h      # Template for WiFi network credentials
└── src/
    ├── config.h                # Server IP, port, pin allocations & constants
    ├── main.cpp                # Setup, loop, WiFi connection, web server & timer logic
    ├── sensors.h               # Sensor data structures & function declarations
    ├── sensors.cpp             # Sensor initialization, reading routines & JSON builder
    └── wifi_config.h           # Local WiFi configuration (do not commit passwords!)
```

---

## 3. JSON Contract Format

The firmware sends data every 60 seconds to `http://<BACKEND_IP>:5000/api/sensor-data`:

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

## 4. Setup & Flashing Instructions

1. **Install PlatformIO or Arduino IDE**:
   - Install the ESP32 board package (version 2.0+).
2. **Install Required Libraries**:
   - `DHT sensor library` (Adafruit)
   - `Adafruit Unified Sensor`
   - `ArduinoJson` (v6 or higher)
3. **Configure WiFi & Backend IP**:
   - Copy `wifi_config_template.h` to `wifi_config.h`.
   - Set your WiFi SSID and Password in `wifi_config.h`.
   - Update `BACKEND_IP` in `src/config.h` to your Flask server's IP address.
4. **Compile & Upload**:
   - Upload code to the ESP32 node.
   - Open Serial Monitor at **115200 Baud** to inspect debugging outputs for each sensor.

---

## 5. UV Scan Triggering Methods

- **Physical Push Button**: Pressing the button connected to `GPIO 13` activates the UV LED array on `GPIO 25` for 5 seconds.
- **Local HTTP Endpoint**: Send a `GET` or `POST` request to `http://<ESP32_IP>/trigger-uv` to activate the UV LEDs remotely.
