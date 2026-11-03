# Grain Guardian — ESP32 DevKit Firmware & Wiring Specification

This directory contains the production-grade ESP32 DevKit firmware for the **Grain Guardian** IoT system. The firmware interfaces with physical sensors, drives an I2C 16x2 LCD display, manages hardware-interlocked dual relay channels (White Light / 365nm UV Light), and communicates with the Render Flask API over Wi-Fi.

---

## 1. Hardware Pinout & Wiring Connections

### ESP32 DevKit (30-pin / 38-pin Board)

| Hardware Component | Component Pin | ESP32 Pin | Interface | Power Requirement | Technical Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DHT22** | DATA (Pin 2) | `GPIO 4` | 1-Wire Digital | 3.3V or 5V | Include 10kΩ pull-up resistor between DATA and 3.3V. |
| **MQ-2 Gas Sensor** | A0 (Analog Out) | `GPIO 34` | Analog (ADC1_CH6) | 5.0V (VCC) | Requires ADC1 (Wi-Fi safe). Allow 2-minute pre-heat for steady baseline. |
| **Capacitive Moisture V1.2**| AOUT (Analog) | `GPIO 35` | Analog (ADC1_CH7) | 3.3V (VCC) | ADC1 channel. Submerge probe in grain bed to measurement line. |
| **Relay Channel 1 (White Light)**| IN1 | `GPIO 26` | Digital Output | 5.0V (VCC) | Active-LOW: Default closed/energized on power-up (White Light ON). |
| **Relay Channel 2 (UV Light)** | IN2 | `GPIO 25` | Digital Output | 5.0V (VCC) | Active-LOW: Default open/de-energized on power-up (UV Light OFF). |
| **16x2 I2C LCD Display** | SDA | `GPIO 21` | I2C Data | 5.0V (VCC) | Default I2C address `0x27` (fallback `0x3F`). |
| **16x2 I2C LCD Display** | SCL | `GPIO 22` | I2C Clock | 5.0V (VCC) | Hardware I2C bus. |
| **Common Ground** | GND | `GND` | Ground | Common Ground | Tie all sensor and relay grounds to ESP32 GND. |

---

## 2. Relay Interlock & Mutual Exclusion Architecture

To protect biological grain samples, operator eye safety, and power rails:
* **Default Operating State**: White Light = **ON**, UV Light = **OFF**.
* **Hardware & Software Interlock**:
  - When UV Light turns ON: White Light is switched OFF immediately *before* UV is energized.
  - When UV Light turns OFF: UV is de-energized *before* White Light is restored.
  - White and UV are **NEVER** energized simultaneously under any command condition.
  - UV defaults to **OFF** after device reboot or power cycle.
  - In `config.h`, set `#define RELAY_ACTIVE_LOW true` for standard optocoupled relay modules.

---

## 3. LCD Display State Machine

The 16x2 I2C LCD uses a non-blocking timed state machine:
* **Normal Operating Mode**:
  - Screen 1: `T:24.5C H:58%` (Row 0) and `M:13.2% G:95` (Row 1).
  - Screen 2: `GRAIN: WHEAT` (Row 0) and `LIGHT: WHITE ON` / `LIGHT: UV ON` (Row 1).
* **Actuator Transition Alert**:
  - Displays `ACTUATOR EVENT:` (Row 0) and `UV LIGHT: ON` or `UV LIGHT: OFF` (Row 1) for 2.5 seconds, then returns smoothly to normal telemetry without full-screen clear flicker.

---

## 4. Software Dependencies & Libraries

Install via PlatformIO (`platformio.ini`) or Arduino IDE Library Manager:
* `bblanchon/ArduinoJson` (v6.21.3+)
* `adafruit/DHT sensor library` (v1.4.6+)
* `adafruit/Adafruit Unified Sensor` (v1.1.14+)
* `marcoschwartz/LiquidCrystal_I2C` (v1.1.4+)
* `WiFi` & `HTTPClient` (bundled with ESP32 Arduino Core v2.0+)

---

## 5. Setup & Flashing Instructions

1. **Configure Wi-Fi Credentials**:
   - Copy `wifi_config_template.h` to `src/wifi_config.h`.
   - Enter your Wi-Fi network SSID and Password:
     ```cpp
     #define WIFI_SSID "AA"
     #define WIFI_PASSWORD "1357924680"
     ```
2. **Configure Backend Target**:
   - In `src/config.h`, set `BACKEND_HOST` to your computer's local Wi-Fi IP (e.g. `"192.168.1.100"`) for local testing or `"grain-guardian-api.onrender.com"` for production.
   - Set `BACKEND_PORT` to `5000` (or `443` for HTTPS).
3. **Build & Upload**:
   - **PlatformIO**: Run `pio run --target upload` and `pio device monitor`.
   - **Arduino IDE**: Select board **"ESP32 Dev Module"**, Baud Rate **115200**.
