#ifndef SENSORS_H_
#define SENSORS_H_

#include <Arduino.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include "config.h"

// Struct representing the final JSON payload expected by the backend
struct SensorData {
  int storageUnitId;
  String grainType;
  float temperature;    // DHT22, in Deg C
  float humidity;       // DHT22, in % RH
  int gasIndex;         // MQ-135 Gas Index (baseline-relative)
  float moisture;       // Calibrated capacitive probe percentage
};

// Global sensor instance references
extern DHT dht;

// Function declarations
bool initSensors();
SensorData readAllSensors();
float calibrateMoisture(int rawValue);
String buildSensorJsonPayload(const SensorData& data);

#endif // SENSORS_H_
