#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WebServer.h>

#include "config.h"
#include "wifi_config.h"
#include "sensors.h"

// Web Server instance listening on Port 80 for trigger requests
WebServer server(80);

// Global Variables
unsigned long lastSensorReadTime = 0;
bool isUvActive = false;
unsigned long uvStartTime = 0;

/**
 * Turns ON the UV LED Array for 5 seconds.
 */
void triggerUvLight() {
  Serial.println("[ACTUATOR] Triggering 365nm UV LED Array for scan...");
  digitalWrite(UV_LED_PIN, HIGH);
  isUvActive = true;
  uvStartTime = millis();
}

/**
 * Checks if the 5-second UV LED duration has elapsed and turns off the LED array.
 */
void checkUvTimer() {
  if (isUvActive && (millis() - uvStartTime >= UV_SCAN_DURATION_MS)) {
    digitalWrite(UV_LED_PIN, LOW);
    isUvActive = false;
    Serial.println("[ACTUATOR] UV LED Array deactivated.");
  }
}

/**
 * Connects ESP32 to local WiFi access point.
 */
void setupWiFi() {
  Serial.printf("[WiFi] Connecting to %s ", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected successfully!");
    Serial.print("[WiFi] ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Connection failed! Proceeding with offline sensor monitoring...");
  }
}

/**
 * Handles incoming web request to trigger UV scan via HTTP GET/POST:
 * http://<ESP32_IP>/trigger-uv
 */
void handleTriggerUvEndpoint() {
  triggerUvLight();
  server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"UV light activated for 5 seconds\"}");
}

/**
 * Handles unknown web server endpoints.
 */
void handleNotFound() {
  server.send(404, "text/plain", "Endpoint Not Found");
}

/**
 * Sends sensor data JSON to backend endpoint via HTTP POST.
 */
void sendSensorDataToBackend(const SensorData& data) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] WiFi not connected. Skipping data upload.");
    return;
  }

  HTTPClient http;
  String targetUrl = "http://" + String(BACKEND_IP) + ":" + String(BACKEND_PORT) + String(BACKEND_ENDPOINT);
  
  Serial.printf("[HTTP] Transmitting sensor data to %s ...\n", targetUrl.c_str());

  String jsonPayload = buildSensorJsonPayload(data);
  Serial.println("[HTTP] Payload: " + jsonPayload);

  http.begin(targetUrl);
  http.addHeader("Content-Type", "application/json");

  int httpResponseCode = http.POST(jsonPayload);

  if (httpResponseCode > 0) {
    Serial.printf("[HTTP] Data sent successfully! Response code: %d\n", httpResponseCode);
    String responseStr = http.getString();
    Serial.println("[HTTP] Response payload: " + responseStr);
  } else {
    Serial.printf("[HTTP] Error sending POST request: %s (code %d)\n", http.errorToString(httpResponseCode).c_str(), httpResponseCode);
  }

  http.end();
}

void setup() {
  // Initialize Serial interface for debugging
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n==========================================");
  Serial.println("  GRAIN GUARDIAN - ESP32 IoT Node");
  Serial.println("==========================================");

  // Initialize hardware pins
  pinMode(UV_LED_PIN, OUTPUT);
  digitalWrite(UV_LED_PIN, LOW); // Start with UV LEDs OFF

  pinMode(BUTTON_PIN, INPUT_PULLUP); // Physical trigger button

  // Initialize sensor suite
  initSensors();

  // Connect WiFi
  setupWiFi();

  // Setup Local HTTP Web Server endpoints for manual/remote UV light trigger
  server.on("/trigger-uv", handleTriggerUvEndpoint);
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("[HTTP Server] Local server listening on port 80");
}

void loop() {
  // 1. Handle HTTP server requests
  server.handleClient();

  // 2. Check physical button press for triggering UV scan
  if (digitalRead(BUTTON_PIN) == LOW) { // Button pressed (active LOW)
    delay(50); // Debounce
    if (digitalRead(BUTTON_PIN) == LOW) {
      Serial.println("[BUTTON] Physical button pressed!");
      triggerUvLight();
      while (digitalRead(BUTTON_PIN) == LOW) {
        delay(10); // Wait for button release
      }
    }
  }

  // 3. Manage UV LED auto-off timer
  checkUvTimer();

  // 4. Periodic sensor reading & data transmission (Every 60s)
  unsigned long currentMillis = millis();
  if (currentMillis - lastSensorReadTime >= SENSOR_READ_INTERVAL_MS || lastSensorReadTime == 0) {
    lastSensorReadTime = currentMillis;

    // Read all sensors
    SensorData currentReadings = readAllSensors();

    // Send payload to backend
    sendSensorDataToBackend(currentReadings);
  }
}
