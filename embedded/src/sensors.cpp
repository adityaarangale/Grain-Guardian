#include "sensors.h"

// Instantiate sensor objects
DHT dht(DHT_PIN, DHT_TYPE);

/**
 * Initializes all sensor interfaces (DHT22, analog pins).
 * Prints serial debugging details for each step.
 */
bool initSensors() {
  Serial.println("[Sensors] Initializing sensor hardware...");

  // 1. Initialize DHT22 (Temp & Humidity)
  dht.begin();
  Serial.println("[Sensors] SUCCESS: DHT22 initialized.");

  // 2. Analog pins (MQ-135 Gas Index and Capacitive Moisture Probe V1.2)
  pinMode(MQ135_ANALOG_PIN, INPUT);
  pinMode(MOISTURE_ANALOG_PIN, INPUT);
  Serial.println("[Sensors] SUCCESS: Analog pins configured (MQ-135 pin " + String(MQ135_ANALOG_PIN) + ", Moisture pin " + String(MOISTURE_ANALOG_PIN) + ").");

  return true;
}

/**
 * Capacitive grain moisture calibration.
 * Converts raw ADC values (0 - 4095 on ESP32) into grain moisture percentage (e.g. 8.0% - 25.0%).
 */
float calibrateMoisture(int rawValue) {
  if (rawValue <= 0) return 0.0;
  
  float moisturePct = map(rawValue, 3200, 1500, 80, 250) / 10.0f;
  
  // Constrain value between realistic grain storage boundaries
  if (moisturePct < 5.0f) moisturePct = 5.0f;
  if (moisturePct > 35.0f) moisturePct = 35.0f;
  
  return moisturePct;
}

/**
 * Reads data from all connected sensors and prints individual debug outputs.
 */
SensorData readAllSensors() {
  SensorData data;
  data.storageUnitId = STORAGE_UNIT_ID;
  data.grainType = GRAIN_TYPE;

  Serial.println("\n--- [SENSOR READ START] ---");

  // 1. DHT22 Reading
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  if (!isnan(temp) && !isnan(hum)) {
    data.temperature = temp;
    data.humidity = hum;
    Serial.printf("  [DHT22] Temp: %.2f °C | Humidity: %.2f %%\n", data.temperature, data.humidity);
  } else {
    data.temperature = 25.0; // Fallback safe default on sensor read failure
    data.humidity = 60.0;
    Serial.println("  [DHT22] ERROR: Failed to read from DHT22, using defaults.");
  }

  // 2. MQ-135 Gas Index Reading
  int rawGas = analogRead(MQ135_ANALOG_PIN);
  data.gasIndex = rawGas > 0 ? rawGas : 110;
  Serial.printf("  [MQ-135] Gas Index: %d\n", data.gasIndex);

  // 3. Capacitive Moisture Probe V1.2 Reading
  int rawMoisture = analogRead(MOISTURE_ANALOG_PIN);
  data.moisture = calibrateMoisture(rawMoisture);
  Serial.printf("  [Moisture Probe] Raw ADC: %d -> Calibrated Grain Moisture: %.1f %%\n", rawMoisture, data.moisture);

  Serial.println("--- [SENSOR READ END] ---\n");

  return data;
}

/**
 * Builds the EXACT JSON payload expected by the Grain Guardian Backend API.
 * Final Contract Schema:
 * {
 *   "storage_unit_id": 1,
 *   "grain_type": "wheat",
 *   "temperature": 28.5,
 *   "humidity": 62.0,
 *   "gas_index": 412,
 *   "moisture": 13.2
 * }
 */
String buildSensorJsonPayload(const SensorData& data) {
  StaticJsonDocument<256> doc;

  doc["storage_unit_id"] = data.storageUnitId;
  doc["grain_type"] = data.grainType;
  doc["temperature"] = serialized(String(data.temperature, 1));
  doc["humidity"] = serialized(String(data.humidity, 1));
  doc["gas_index"] = data.gasIndex;
  doc["moisture"] = serialized(String(data.moisture, 1));

  String jsonOutput;
  serializeJson(doc, jsonOutput);
  return jsonOutput;
}
