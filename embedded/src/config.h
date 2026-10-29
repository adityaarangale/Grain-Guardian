#ifndef CONFIG_H_
#define CONFIG_H_

// ==========================================
// Network & Backend Configuration
// ==========================================
// IP address or hostname of the Grain Guardian Backend server
#define BACKEND_IP "192.168.1.100"
#define BACKEND_PORT 5000
#define BACKEND_ENDPOINT "/api/sensor-data"

// Storage Unit Metadata
#define STORAGE_UNIT_ID 1
#define GRAIN_TYPE "wheat"

// Data Transmission Interval (milliseconds)
#define SENSOR_READ_INTERVAL_MS 60000

// ==========================================
// Hardware Pin Definitions (ESP32)
// ==========================================

// DHT22 Digital Temperature & Humidity Sensor
#define DHT_PIN 4
#define DHT_TYPE DHT22

// Analog Input Pins
#define MQ135_ANALOG_PIN 34     // MQ-135 Gas Index Sensor (ADC1 Channel 6)
#define MOISTURE_ANALOG_PIN 35  // Capacitive grain moisture probe V1.2 (ADC1 Channel 7)

// Digital Actuator Pins
#define UV_LED_PIN 25           // Relay/MOSFET control for 365nm UV LED Array
#define BUTTON_PIN 13           // Physical push button to trigger UV scan (Internal Pullup)

// UV Scan Duration
#define UV_SCAN_DURATION_MS 5000

#endif // CONFIG_H_
