#ifndef SENSORS_H_
#define SENSORS_H_

#include <Arduino.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include "config.h"

// Struct representing the live sensor telemetry contract
struct SensorData {
  int storageUnitId;
  String grainType;
  float temperature;    // DHT22, in Deg C (0.0 if not sensed)
  float humidity;       // DHT22, in % RH (0.0 if not sensed)
  int gasIndex;         // MQ-2 normalized gas-response index (0 if not sensed)
  float moisture;       // Calibrated capacitive probe percentage (0.0 if not sensed)
  int rawMoisture;      // Raw ADC reading (0-4095)
  int mq2Raw;           // Raw MQ-2 analog ADC reading
  bool isCalibrated;    // Calibration validity status
  bool dhtValid;        // True if valid DHT reading was sensed
};

// Global sensor instance references
extern DHT dht;

// Function declarations
bool initSensors();
SensorData readAllSensors();
float calibrateMoisture(int rawValue);
int calculateMq2Index(int rawValue);
String buildSensorJsonPayload(const SensorData& data);

#endif // SENSORS_H_
