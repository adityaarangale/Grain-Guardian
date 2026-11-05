#include <Arduino.h>
#include <WiFi.h>
#include <WiFiMulti.h>
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

// WiFiMulti instance for automatic multi-network roaming and reconnection
WiFiMulti wifiMulti;

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

    // Break-before-make safety interlock
    delay(50);

    // 2. Turn ON UV Light (drives both GPIO 27 and GPIO 25 to guarantee actuation)
    digitalWrite(RELAY_UV_LIGHT_PIN, RELAY_STATE_ON);
    digitalWrite(RELAY_UV_LIGHT_PIN_ALT, RELAY_STATE_ON);
    currentUvLight = true;
    Serial.println("[ACTUATOR] Relays Switched: White = OFF, UV = ON (GPIO 27 & 25 active)");
    triggerLcdAlert("UV LIGHT: ON");
  } else {
    // 1. Immediately turn OFF UV Light (both GPIO 27 and GPIO 25)
    digitalWrite(RELAY_UV_LIGHT_PIN, RELAY_STATE_OFF);
    digitalWrite(RELAY_UV_LIGHT_PIN_ALT, RELAY_STATE_OFF);
    currentUvLight = false;

    // Break-before-make pause
    delay(50);

    // 2. Restore White Light ON
    digitalWrite(RELAY_WHITE_LIGHT_PIN, RELAY_STATE_ON);
    currentWhiteLight = true;
    Serial.println("[ACTUATOR] Relays Switched: White = ON, UV = OFF");
    triggerLcdAlert("UV LIGHT: OFF");
  }
}

const char* getWiFiStatusString(wl_status_t status) {
  switch (status) {
    case WL_IDLE_STATUS:     return "IDLE_STATUS (Searching/Waiting)";
    case WL_NO_SSID_AVAIL:   return "NO_SSID_AVAIL (SSID not found! Check 2.4 GHz band)";
    case WL_SCAN_COMPLETED:  return "SCAN_COMPLETED";
    case WL_CONNECTED:       return "CONNECTED";
    case WL_CONNECT_FAILED:  return "CONNECT_FAILED (Password incorrect?)";
    case WL_CONNECTION_LOST: return "CONNECTION_LOST (Signal dropped)";
    case WL_DISCONNECTED:    return "DISCONNECTED (Not connected)";
    default:                 return "UNKNOWN_STATUS";
  }
}

/**
 * Connects to Wi-Fi using WiFiMulti with 2.4 GHz channel diagnostics and LCD feedback.
 * Supports up to 3 configured networks with auto-fallback and generous timeout (up to 20s).
 */
void setupWiFi() {
  Serial.println("\n[WiFi] ==========================================");
  Serial.println("[WiFi]   Initializing Wi-Fi Radio (2.4 GHz)");
  Serial.println("[WiFi] ==========================================");

  // Display initial Wi-Fi setup status on I2C LCD
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("WiFi Connecting ");
  lcd.setCursor(0, 1);
  lcd.print("SSID: ");
  lcd.print(WIFI_SSID);

  // Reset radio to known clean station state
  WiFi.disconnect(true);
  delay(100);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);
  WiFi.setSleep(false); // Disable modem sleep to prevent dropped hotspot packets

  // 1. Diagnostic scan of nearby 2.4 GHz Wi-Fi networks
  Serial.println("[WiFi] Scanning nearby 2.4 GHz Wi-Fi networks...");
  int n = WiFi.scanNetworks();
  if (n <= 0) {
    Serial.println("[WiFi] No networks found in scan! Ensure router or mobile hotspot is broadcasting on 2.4 GHz.");
  } else {
    Serial.printf("[WiFi] Found %d Wi-Fi networks in range:\n", n);
    bool primaryFound = false;
    for (int i = 0; i < n && i < 10; ++i) {
      Serial.printf("  (%d) %-20s [RSSI: %4d dBm, Ch: %2d]\n",
                    i + 1, WiFi.SSID(i).c_str(), WiFi.RSSI(i), WiFi.channel(i));
      if (WiFi.SSID(i).equals(WIFI_SSID)) {
        primaryFound = true;
      }
    }
    if (primaryFound) {
      Serial.printf("[WiFi] >> Target SSID '%s' IS DETECTED in the air! Proceeding to connect...\n", WIFI_SSID);
    } else {
      Serial.printf("[WiFi] >> WARNING: Target SSID '%s' WAS NOT FOUND in scan!\n", WIFI_SSID);
      Serial.println("[WiFi] >> NOTE: If using a phone hotspot, ensure:");
      Serial.println("[WiFi]    - iOS: Settings -> Personal Hotspot -> 'Maximize Compatibility' = ON");
      Serial.println("[WiFi]    - Android: Hotspot Settings -> AP Band = '2.4 GHz'");
    }
  }

  // 2. Register known networks with WiFiMulti
  wifiMulti.addAP(WIFI_SSID, WIFI_PASSWORD);
#ifdef WIFI_SSID_2
  if (strlen(WIFI_SSID_2) > 0) wifiMulti.addAP(WIFI_SSID_2, WIFI_PASSWORD_2);
#endif
#ifdef WIFI_SSID_3
  if (strlen(WIFI_SSID_3) > 0) wifiMulti.addAP(WIFI_SSID_3, WIFI_PASSWORD_3);
#endif

  // Direct begin for robust initial connection
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  // 3. Wait up to 40 attempts (20 seconds) with live LCD animation
  int attempts = 0;
  const int maxAttempts = 40;
  while (WiFi.status() != WL_CONNECTED && attempts < maxAttempts) {
    delay(500);
    Serial.print(".");
    attempts++;

    // Animated dots on LCD Line 0
    lcd.setCursor(14, 0);
    switch (attempts % 4) {
      case 0: lcd.print("   "); break;
      case 1: lcd.print(".  "); break;
      case 2: lcd.print(".. "); break;
      case 3: lcd.print("..."); break;
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected successfully!");
    Serial.print("[WiFi] Assigned IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("[WiFi] Signal Strength (RSSI): ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");

    // Success screen on LCD
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi Connected! ");
    lcd.setCursor(0, 1);
    lcd.print(WiFi.localIP().toString());
    delay(1500);
  } else {
    wl_status_t finalStatus = WiFi.status();
    Serial.printf("\n[WiFi] Initial connection failed! Status: %s\n", getWiFiStatusString(finalStatus));
    Serial.println("[WiFi] ESP32 will continue in local autonomous mode and auto-retry in the background.");

    // Failure screen on LCD
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi FAILED!    ");
    lcd.setCursor(0, 1);
    lcd.print("Local Mode (NoW)");
    delay(1500);
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
      Serial.println("[WiFi] Background reconnect attempt via WiFiMulti...");

      if (wifiMulti.run(4000) == WL_CONNECTED) {
        Serial.print("[WiFi] Reconnected successfully! IP: ");
        Serial.println(WiFi.localIP());
        triggerLcdAlert("WiFi Reconnected");
      } else {
        // Fallback re-issue begin
        WiFi.disconnect(false);
        delay(50);
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
        Serial.printf("[WiFi] Background reconnect status: %s\n", getWiFiStatusString(WiFi.status()));
      }
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
    // Shows actual values when sensed; displays 0 when sensor does not sense anything / disconnected
    char tempStr[10];
    char humStr[10];
    char moistStr[10];
    char gasStr[10];

    // Temperature: Show value if sensed, otherwise 0
    if (latestReadings.dhtValid && latestReadings.temperature > 0.0f) {
      snprintf(tempStr, sizeof(tempStr), "%.1fC", latestReadings.temperature);
    } else {
      snprintf(tempStr, sizeof(tempStr), "0");
    }

    // Humidity: Show value if sensed, otherwise 0
    if (latestReadings.dhtValid && latestReadings.humidity > 0.0f) {
      snprintf(humStr, sizeof(humStr), "%.0f%%", latestReadings.humidity);
    } else {
      snprintf(humStr, sizeof(humStr), "0");
    }

    // Moisture: Show value if sensed, otherwise 0
    if (latestReadings.moisture > 0.0f) {
      snprintf(moistStr, sizeof(moistStr), "%.1f%%", latestReadings.moisture);
    } else {
      snprintf(moistStr, sizeof(moistStr), "0");
    }

    // Gas: Show value if sensed, otherwise 0
    if (latestReadings.gasIndex > 0) {
      snprintf(gasStr, sizeof(gasStr), "%d", latestReadings.gasIndex);
    } else {
      snprintf(gasStr, sizeof(gasStr), "0");
    }

    const char* wifiTag = (WiFi.status() == WL_CONNECTED) ? "[W]" : "[!]";
    snprintf(line0, sizeof(line0), "T:%-4s H:%-4s %s", tempStr, humStr, wifiTag);
    snprintf(line1, sizeof(line1), "M:%-5s  G:%-5s", moistStr, gasStr);
  } else {
    // Page 2: Grain Info & Active Light Status + Wi-Fi Connectivity
    snprintf(line0, sizeof(line0), "GRAIN: %-9s", latestReadings.grainType.c_str());
    const char* wifiState = (WiFi.status() == WL_CONNECTED) ? "ONLINE" : "NO-NET";
    if (currentUvLight) {
      snprintf(line1, sizeof(line1), "L:UV-ON  W:%-6s", wifiState);
    } else {
      snprintf(line1, sizeof(line1), "L:WH-ON  W:%-6s", wifiState);
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

  // 1. Initialize Relays & Perform Hardware Self-Test (Audible Click Verification)
  pinMode(RELAY_WHITE_LIGHT_PIN, OUTPUT);
  pinMode(RELAY_UV_LIGHT_PIN, OUTPUT);
  pinMode(RELAY_UV_LIGHT_PIN_ALT, OUTPUT);

  Serial.println("[Relays] Running Boot Hardware Self-Test...");
  // Test Channel 1 (White)
  digitalWrite(RELAY_WHITE_LIGHT_PIN, RELAY_STATE_ON);
  delay(300);
  digitalWrite(RELAY_WHITE_LIGHT_PIN, RELAY_STATE_OFF);
  delay(200);

  // Test Channel 2 (UV)
  digitalWrite(RELAY_UV_LIGHT_PIN, RELAY_STATE_ON);
  digitalWrite(RELAY_UV_LIGHT_PIN_ALT, RELAY_STATE_ON);
  delay(300);
  digitalWrite(RELAY_UV_LIGHT_PIN, RELAY_STATE_OFF);
  digitalWrite(RELAY_UV_LIGHT_PIN_ALT, RELAY_STATE_OFF);
  delay(200);

  // Settle into Default Safe State: White Light ON, UV Light OFF
  digitalWrite(RELAY_WHITE_LIGHT_PIN, RELAY_STATE_ON);
  currentWhiteLight = true;
  currentUvLight = false;
  Serial.println("[Relays] Self-test complete. Safe state active: White ON, UV OFF.");

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

  // 6. Serial Debug Command Listener (Allows instant manual testing via Serial Monitor)
  // Send 'W' or 'w' to toggle White Light; 'U' or 'u' to toggle UV Light; 'T' or 't' for Relay Test Cycle
  if (Serial.available() > 0) {
    char ch = Serial.read();
    if (ch == 'w' || ch == 'W') {
      Serial.println("[SERIAL CMD] Toggle White Light requested.");
      setLights(!currentWhiteLight, false);
    } else if (ch == 'u' || ch == 'U') {
      Serial.println("[SERIAL CMD] Toggle UV Light requested.");
      setLights(false, !currentUvLight);
    } else if (ch == 't' || ch == 'T') {
      Serial.println("[SERIAL CMD] Running full relay cycle test...");
      setLights(true, false);
      delay(800);
      setLights(false, true);
      delay(800);
      setLights(true, false);
      Serial.println("[SERIAL CMD] Test cycle complete (White restored).");
    }
  }
}
