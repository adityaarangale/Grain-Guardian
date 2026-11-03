#ifndef CONFIG_H_
#define CONFIG_H_

#include <Arduino.h>

// ==========================================
// 1. Network & Backend REST API Configuration
// ==========================================
// Production Render URL
#define BACKEND_BASE_URL "https://grain-guardian-api.onrender.com"
#define BACKEND_HOST "grain-guardian-api.onrender.com"
#define BACKEND_PORT 443
#define USE_HTTPS true

// Endpoint URLs
#define ENDPOINT_SENSOR_DATA    "/api/sensor-data"
#define ENDPOINT_HEARTBEAT      "/api/device/heartbeat"
#define ENDPOINT_COMMAND_POLL   "/api/device/command"
#define ENDPOINT_COMMAND_RESULT "/api/device/command-result"

// Device Identity & Security
#define DEVICE_ID "esp32-devkit"
#define FIRMWARE_VERSION "1.2.0"
#define DEVICE_TOKEN "grain-guardian-device-token-2026"

// Storage Silo Metadata
#define STORAGE_UNIT_ID 1
#define GRAIN_TYPE "wheat"

// ==========================================
// 2. Non-Blocking Timing Intervals (ms)
// ==========================================
#define SENSOR_READ_INTERVAL_MS   2500  // Telemetry publish interval (2-3 seconds)
#define HEARTBEAT_INTERVAL_MS     5000  // Device heartbeat interval (5 seconds)
#define COMMAND_POLL_INTERVAL_MS  1500  // Actuation command poll (1-2 seconds)
#define LCD_CYCLE_INTERVAL_MS     3000  // Rotate LCD info screen every 3 seconds
#define LCD_OVERLAY_DURATION_MS   2500  // Temporary UV status alert display (2.5 seconds)
#define WIFI_RETRY_INTERVAL_MS    10000 // Retry Wi-Fi reconnect every 10s if disconnected

// ==========================================
// 3. Hardware Pin Definitions (ESP32 DevKit)
// ==========================================
// DHT22 Digital Temperature & Humidity Sensor
#define DHT_PIN 4
#define DHT_TYPE DHT22

// Analog Input Sensors (ADC1 only, compatible with active Wi-Fi)
#define MQ2_ANALOG_PIN          34  // MQ-2 Gas Sensor Analog Output (ADC1_CH6)
#define MOISTURE_ANALOG_PIN     35  // Capacitive Grain Moisture Probe V1.2 (ADC1_CH7)

// 2-Channel Relay Actuators (Hardware Interlocked)
#define RELAY_WHITE_LIGHT_PIN   26  // Relay Channel 1: White Chamber Light
#define RELAY_UV_LIGHT_PIN      25  // Relay Channel 2: 365nm UV Fluorescence Light

// Relay Logic: Most 2-channel 5V relay modules are Active LOW (LOW = ON / Closed, HIGH = OFF / Open)
#define RELAY_ACTIVE_LOW        true

#if RELAY_ACTIVE_LOW
  #define RELAY_STATE_ON   LOW
  #define RELAY_STATE_OFF  HIGH
#else
  #define RELAY_STATE_ON   HIGH
  #define RELAY_STATE_OFF  LOW
#endif

// I2C 16x2 LCD Display (LiquidCrystal_I2C)
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22
#define LCD_I2C_ADDR 0x27  // Standard address; use 0x3F if 0x27 does not respond
#define LCD_COLS 16
#define LCD_ROWS 2

// ==========================================
// 4. Sensor Calibration References
// ==========================================
// Capacitive Moisture Probe V1.2 Raw ADC calibration
#define CALIB_MOISTURE_DRY_AIR  3200  // Raw ADC in dry air (5.0% moisture baseline)
#define CALIB_MOISTURE_SATURATED 1500 // Raw ADC in saturated medium (35.0% moisture)

// MQ-2 Clean Air Baseline Reference
#define CALIB_MQ2_CLEAN_AIR 75

#endif // CONFIG_H_
