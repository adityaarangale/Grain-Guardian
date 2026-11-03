#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#include "config.h"

#if __has_include("wifi_config.h")
  #include "wifi_config.h"
#elif __has_include("../wifi_config_template.h")
  #include "../wifi_config_template.h"
#else
  #define WIFI_SSID "AA"
  #define WIFI_PASSWORD "1357924680"
#endif

#include "sensors.h"

// Instantiate I2C LCD Display (16x2)
LiquidCrystal_I2C lcd(LCD_I2C_ADDR, LCD_COLS, LCD_ROWS);

// Hardware Actuation State (Default: White Light ON, UV Light OFF)
bool currentWhiteLight = true;
bool currentUvLight = false;

// LCD Display State Machine
enum LcdState {
  LCD_NORMAL_PAGE_1,
  LCD_NORMAL_PAGE_2,
  LCD_ALERT_OVERLAY
};

LcdState currentLcdState = LCD_NORMAL_PAGE_1;
unsigned long lcdStateStartTime = 0;
unsigned long lastLcdUpdate = 0;
String lcdAlertMessage = "";

// Non-blocking Task Timers
unsigned long lastSensorReadTime = 0;
unsigned long lastHeartbeatTime = 0;
unsigned long lastCommandPollTime = 0;
unsigned long lastWifiRetryTime = 0;

// Cached Latest Sensor Telemetry
SensorData latestReadings;

/**
 * Triggers a temporary 2.5-second alert screen on the LCD without blocking delays.
 */
void triggerLcdAlert(const String& message) {
  lcdAlertMessage = message;
  currentLcdState = LCD_ALERT_OVERLAY;
  lcdStateStartTime = millis();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ACTUATOR EVENT:");
  lcd.setCursor(0, 1);
  lcd.print(message);
}

/**
 * Hardware Light Actuation with Strict Mutual Exclusion:
 * - Default safe state: White ON, UV OFF.
 * - When UV turns ON: White turns OFF first.
 * - When UV turns OFF: White turns ON.
 * - Both lights are NEVER permitted to be active simultaneously.
 */
void setLights(bool whiteOn, bool uvOn) {
  // Strict hardware mutual exclusion
  if (uvOn) {
    whiteOn = false;
  }

  if (uvOn) {
    // 1. Immediately turn OFF White Light
    digitalWrite(RELAY_WHITE_LIGHT_PIN, RELAY_STATE_OFF);
    currentWhiteLight = false;

    // 2. Turn ON UV Light
    digitalWrite(RELAY_UV_LIGHT_PIN, RELAY_STATE_ON);
    currentUvLight = true;
    Serial.println("[ACTUATOR] Relays Switched: White = OFF, UV = ON");
    triggerLcdAlert("UV LIGHT: ON");
  } else {
    // 1. Immediately turn OFF UV Light
    digitalWrite(RELAY_UV_LIGHT_PIN, RELAY_STATE_OFF);
    currentUvLight = false;

    // 2. Restore White Light ON
    digitalWrite(RELAY_WHITE_LIGHT_PIN, RELAY_STATE_ON);
    currentWhiteLight = true;
    Serial.println("[ACTUATOR] Relays Switched: White = ON, UV = OFF");
    triggerLcdAlert("UV LIGHT: OFF");
  }
}

/**
 * Connects to local Wi-Fi with bounded retry (max 15 attempts).
 * Never blocks indefinitely and never prints sensitive credentials.
 */
void setupWiFi() {
  Serial.print("[WiFi] Connecting to Wi-Fi SSID: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 15) {
    delay(400);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected successfully!");
    Serial.print("[WiFi] Assigned IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Initial connection failed. Continuing in local autonomous mode...");
  }
}

/**
 * Periodically attempts Wi-Fi reconnection in background if disconnected.
 */
void maintainWiFiConnection() {
  if (WiFi.status() != WL_CONNECTED) {
    unsigned long now = millis();
    if (now - lastWifiRetryTime >= WIFI_RETRY_INTERVAL_MS) {
      lastWifiRetryTime = now;
      Serial.println("[WiFi] Re-attempting background connection...");
      WiFi.reconnect();
    }
  }
}

/**
 * Formats backend HTTP URL.
 */
String getBackendUrl(const char* endpoint) {
#ifdef BACKEND_BASE_URL
  return String(BACKEND_BASE_URL) + String(endpoint);
#else
  String protocol = USE_HTTPS ? "https://" : "http://";
  String url = protocol + String(BACKEND_HOST) + ":" + String(BACKEND_PORT) + String(endpoint);
  return url;
#endif
}

/**
 * Initiates HTTP connection with TLS support for Render HTTPS endpoints.
 */
bool beginHttpConnection(HTTPClient& http, WiFiClientSecure& secClient, WiFiClient& plainClient, const String& url) {
  if (url.startsWith("https://")) {
    secClient.setInsecure();
    return http.begin(secClient, url);
  } else {
    return http.begin(plainClient, url);
  }
}

/**
 * Transmits sensor telemetry JSON to backend endpoint.
 */
void sendSensorTelemetry(const SensorData& data) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  WiFiClientSecure secClient;
  WiFiClient plainClient;
  String url = getBackendUrl(ENDPOINT_SENSOR_DATA);
  beginHttpConnection(http, secClient, plainClient, url);
  http.setTimeout(3500);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);

  String payload = buildSensorJsonPayload(data);
  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    Serial.printf("[HTTP Telemetry] Sent (%d)\n", httpCode);
  } else {
    Serial.printf("[HTTP Telemetry] Error: %s\n", http.errorToString(httpCode).c_str());
  }
  http.end();
}

/**
 * Sends device heartbeat to backend.
 */
void sendDeviceHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  WiFiClientSecure secClient;
  WiFiClient plainClient;
  String url = getBackendUrl(ENDPOINT_HEARTBEAT);
  beginHttpConnection(http, secClient, plainClient, url);
  http.setTimeout(3000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);

  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["device_type"] = "esp32-devkit";
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["status"] = "online";
  doc["ip_address"] = WiFi.localIP().toString();

  String payload;
  serializeJson(doc, payload);

  int httpCode = http.POST(payload);
  http.end();
}

/**
 * Acknowledges command execution and reports actual relay states to backend.
 */
void acknowledgeCommand(const String& cmdId, bool whiteState, bool uvState) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  WiFiClientSecure secClient;
  WiFiClient plainClient;
  String url = getBackendUrl(ENDPOINT_COMMAND_RESULT);
  beginHttpConnection(http, secClient, plainClient, url);
  http.setTimeout(3000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);

  StaticJsonDocument<256> doc;
  doc["command_id"] = cmdId;
  doc["status"] = "acknowledged";
  doc["white_light"] = whiteState;
  doc["uv_light"] = uvState;
  doc["message"] = "Physical relays switched safely with mutual exclusion.";

  String payload;
  serializeJson(doc, payload);
  http.POST(payload);
  http.end();
}

/**
 * Polls backend for pending light/relay commands (every 1-2s).
 */
void pollDeviceCommands() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  WiFiClientSecure secClient;
  WiFiClient plainClient;
  String url = getBackendUrl(ENDPOINT_COMMAND_POLL);
  beginHttpConnection(http, secClient, plainClient, url);
  http.setTimeout(2500);
  http.addHeader("X-Device-Token", DEVICE_TOKEN);

  int httpCode = http.GET();
  if (httpCode == 200) {
    String response = http.getString();
    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, response);

    if (!err && doc["has_command"] == true) {
      JsonObject cmd = doc["command"];
      String cmdId = cmd["command_id"].as<String>();
      JsonObject params = cmd["params"];

      bool reqWhite = params["white_light"] | false;
      bool reqUv = params["uv_light"] | false;

      Serial.printf("[COMMAND] Processing Command ID: %s | White: %d, UV: %d\n", cmdId.c_str(), reqWhite, reqUv);

      // Execute physical actuation safely
      setLights(reqWhite, reqUv);

      // Acknowledge execution with actual states
      acknowledgeCommand(cmdId, currentWhiteLight, currentUvLight);
    }
  }
  http.end();
}

/**
 * Updates LCD screen with anti-flicker buffered string formatting.
 */
void updateLcdDisplay() {
  unsigned long now = millis();

  // Manage temporary Alert Overlay timing (2.5s duration)
  if (currentLcdState == LCD_ALERT_OVERLAY) {
    if (now - lcdStateStartTime >= LCD_OVERLAY_DURATION_MS) {
      currentLcdState = LCD_NORMAL_PAGE_1;
      lcd.clear();
    } else {
      return; // Keep displaying alert without refreshing
    }
  }

  // Rotate between normal pages every LCD_CYCLE_INTERVAL_MS
  if (now - lastLcdUpdate >= LCD_CYCLE_INTERVAL_MS) {
    lastLcdUpdate = now;
    currentLcdState = (currentLcdState == LCD_NORMAL_PAGE_1) ? LCD_NORMAL_PAGE_2 : LCD_NORMAL_PAGE_1;
  }

  char line0[17];
  char line1[17];

  if (currentLcdState == LCD_NORMAL_PAGE_1) {
    // Page 1: Temperature & Humidity / Moisture & Gas
    snprintf(line0, sizeof(line0), "T:%.1fC H:%.0f%%   ", latestReadings.temperature, latestReadings.humidity);
    snprintf(line1, sizeof(line1), "M:%.1f%% G:%-4d   ", latestReadings.moisture, latestReadings.gasIndex);
  } else {
    // Page 2: Grain Info & Active Light Status
    snprintf(line0, sizeof(line0), "GRAIN: %-9s", latestReadings.grainType.c_str());
    if (currentUvLight) {
      snprintf(line1, sizeof(line1), "LIGHT: UV ON    ");
    } else {
      snprintf(line1, sizeof(line1), "LIGHT: WHITE ON ");
    }
  }

  lcd.setCursor(0, 0);
  lcd.print(line0);
  lcd.setCursor(0, 1);
  lcd.print(line1);
}

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n==========================================");
  Serial.println("  GRAIN GUARDIAN - ESP32 DevKit Node");
  Serial.println("  Firmware Version: 1.2.0");
  Serial.println("==========================================");

  // 1. Initialize Relays (Default Safe State: White Light ON, UV Light OFF)
  pinMode(RELAY_WHITE_LIGHT_PIN, OUTPUT);
  pinMode(RELAY_UV_LIGHT_PIN, OUTPUT);

  // Always force UV to OFF after reset
  digitalWrite(RELAY_UV_LIGHT_PIN, RELAY_STATE_OFF);
  currentUvLight = false;

  // Restore White Light to ON
  digitalWrite(RELAY_WHITE_LIGHT_PIN, RELAY_STATE_ON);
  currentWhiteLight = true;
  Serial.println("[Relays] Initialized in Safe State: White ON, UV OFF.");

  // 2. Initialize I2C LCD Display
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("GRAIN GUARDIAN");
  lcd.setCursor(0, 1);
  lcd.print("Initializing...");

  // 3. Initialize Sensor Suite
  initSensors();

  // 4. Connect Wi-Fi with bounded retry
  setupWiFi();

  // 5. Take initial baseline readings
  latestReadings = readAllSensors();

  lcd.clear();
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Maintain Wi-Fi connectivity without blocking sensor routines
  maintainWiFiConnection();

  // 2. Read Sensors & Publish Telemetry (every 2.5 seconds)
  if (currentMillis - lastSensorReadTime >= SENSOR_READ_INTERVAL_MS || lastSensorReadTime == 0) {
    lastSensorReadTime = currentMillis;

    // Read physical hardware sensors
    latestReadings = readAllSensors();

    // Transmit telemetry to backend if Wi-Fi connected
    sendSensorTelemetry(latestReadings);
  }

  // 3. Send Heartbeat to Backend (every 5 seconds)
  if (currentMillis - lastHeartbeatTime >= HEARTBEAT_INTERVAL_MS) {
    lastHeartbeatTime = currentMillis;
    sendDeviceHeartbeat();
  }

  // 4. Poll Actuation Commands from Backend (every 1.5 seconds)
  if (currentMillis - lastCommandPollTime >= COMMAND_POLL_INTERVAL_MS) {
    lastCommandPollTime = currentMillis;
    pollDeviceCommands();
  }

  // 5. Update Local LCD Display (non-blocking timed state machine)
  updateLcdDisplay();
}
