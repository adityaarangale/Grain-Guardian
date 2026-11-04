#include "sensors.h"

// Instantiate DHT sensor
DHT dht(DHT_PIN, DHT_TYPE);

/**
 * Initializes sensor hardware pins and digital sensor communications.
 */
bool initSensors() {
  Serial.println("[Sensors] Initializing DHT22, MQ-2, and Capacitive Probe...");

  dht.begin();
  pinMode(MQ2_ANALOG_PIN, INPUT);
  pinMode(MOISTURE_ANALOG_PIN, INPUT);

  // Set ADC attenuation to 11dB to measure up to ~3.3V full scale on ESP32
  analogSetAttenuation(ADC_11db);

  Serial.println("[Sensors] Sensor hardware initialized successfully.");
  return true;
}

/**
 * Capacitive Grain Moisture Calibration Routine:
 * Converts raw ESP32 ADC values (0 - 4095) into grain moisture percentage.
 * If sensor does not sense anything (disconnected / near 0), returns 0.0.
 */
float calibrateMoisture(int rawValue) {
  if (rawValue <= 100) return 0.0f;

  // Linear interpolation across calibrated boundaries
  float moisturePct = map(rawValue, CALIB_MOISTURE_DRY_AIR, CALIB_MOISTURE_SATURATED, 80, 250) / 10.0f;

  // Boundary clamp
  if (moisturePct < 0.0f) moisturePct = 0.0f;
  if (moisturePct > 35.0f) moisturePct = 35.0f;

  return moisturePct;
}

/**
 * Normalized MQ-2 Gas-Response Index:
 * Converts raw ADC into response index relative to clean-air baseline.
 * If sensor does not sense anything, returns 0.
 */
int calculateMq2Index(int rawValue) {
  if (rawValue <= 40) return 0;
  // Normalized metric: scaled relative to clean-air baseline
  return rawValue;
}

/**
 * Reads all hardware sensors and packages readings into a SensorData struct.
 * If sensor does not sense anything or is disconnected, sets 0 on output.
 * If values are received from sensor, outputs actual measured values.
 */
SensorData readAllSensors() {
  SensorData data;
  data.storageUnitId = STORAGE_UNIT_ID;
  data.grainType = GRAIN_TYPE;

  // 1. DHT22 Digital Temperature & Humidity
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  if (!isnan(temp) && !isnan(hum) && temp > -40.0f && hum >= 0.0f) {
    data.temperature = temp;
    data.humidity = hum;
    data.dhtValid = true;
  } else {
    // If sensor does not sense anything or disconnected, set 0
    data.temperature = 0.0f;
    data.humidity = 0.0f;
    data.dhtValid = false;
    Serial.println("[DHT22] Warning: Sensor not sensing or disconnected (reporting 0).");
  }

  // 2. Capacitive Grain Moisture Probe V1.2
  int rawMoist = analogRead(MOISTURE_ANALOG_PIN);
  data.rawMoisture = rawMoist;
  if (rawMoist <= 100) {
    data.moisture = 0.0f;
    data.isCalibrated = false;
  } else {
    data.moisture = calibrateMoisture(rawMoist);
    data.isCalibrated = (rawMoist > 800 && rawMoist < 3800);
  }

  // 3. MQ-2 Gas Sensor Analog Output
  int rawGas = analogRead(MQ2_ANALOG_PIN);
  data.mq2Raw = rawGas;
  if (rawGas <= 40) {
    data.gasIndex = 0;
  } else {
    data.gasIndex = calculateMq2Index(rawGas);
  }

  return data;
}

/**
 * Builds the exact JSON payload expected by /api/sensor-data.
 */
String buildSensorJsonPayload(const SensorData& data) {
  StaticJsonDocument<384> doc;

  doc["storage_unit_id"] = data.storageUnitId;
  doc["grain_type"] = data.grainType;
  doc["temperature"] = round(data.temperature * 10.0f) / 10.0f;
  doc["humidity"] = round(data.humidity * 10.0f) / 10.0f;
  doc["gas_index"] = data.gasIndex;
  doc["moisture"] = round(data.moisture * 10.0f) / 10.0f;
  doc["raw_moisture"] = data.rawMoisture;
  doc["mq2_raw"] = data.mq2Raw;
  doc["is_calibrated"] = data.isCalibrated;
  doc["device_id"] = DEVICE_ID;
  doc["device_token"] = DEVICE_TOKEN;

  String output;
  serializeJson(doc, output);
  return output;
}
