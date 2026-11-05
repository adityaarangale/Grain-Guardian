#include <Arduino.h>
#include <WiFi.h>
#include <WiFiMulti.h>
#include <WiFiClientSecure.h>
#include "esp_camera.h"
#include "esp_http_server.h"
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

#include "camera_pins.h"
#include "camera_config.h"

#if __has_include("../src/wifi_config.h")
  #include "../src/wifi_config.h"
#elif __has_include("../wifi_config_template.h")
  #include "../wifi_config_template.h"
#else
  #define WIFI_SSID "AA"
  #define WIFI_PASSWORD "1357924680"
#endif

// WiFiMulti instance for automatic multi-network roaming
WiFiMulti wifiMulti;

// HTTP Stream Server Instance
httpd_handle_t stream_httpd = NULL;

#define PART_BOUNDARY "123456789000000000000987654321"
static const char* _STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* _STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* _STREAM_PART = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

unsigned long lastHeartbeatTime = 0;

/**
 * MJPEG Video Stream Handler: Serves continuous JPEG frames over HTTP.
 */
static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;
  char * part_buf[64];

  res = httpd_resp_set_type(req, _STREAM_CONTENT_TYPE);
  if (res != ESP_OK) return res;

  // Add CORS header so browser can render directly
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("[Camera] Error: Camera frame capture failed");
      res = ESP_FAIL;
    } else {
      _jpg_buf_len = fb->len;
      _jpg_buf = fb->buf;
    }

    if (res == ESP_OK) {
      size_t hlen = snprintf((char *)part_buf, 64, _STREAM_PART, _jpg_buf_len);
      res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
    }
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
    }
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
    }

    if (fb) {
      esp_camera_fb_return(fb);
      fb = NULL;
      _jpg_buf = NULL;
    } else if (res != ESP_OK) {
      break;
    }
  }
  return res;
}

/**
 * Single Frame Snapshot Handler (/capture): Serves single JPEG image.
 */
static esp_err_t capture_handler(httpd_req_t *req) {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }

  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=capture.jpg");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

  esp_err_t res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
  esp_camera_fb_return(fb);
  return res;
}

/**
 * Initializes and starts the lightweight HTTP streaming server on Port 81.
 */
void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = STREAM_SERVER_PORT;
  config.ctrl_port = STREAM_SERVER_PORT;

  httpd_uri_t stream_uri = {
    .uri       = "/stream",
    .method    = HTTP_GET,
    .handler   = stream_handler,
    .user_ctx  = NULL
  };

  httpd_uri_t capture_uri = {
    .uri       = "/capture",
    .method    = HTTP_GET,
    .handler   = capture_handler,
    .user_ctx  = NULL
  };

  Serial.printf("[HTTP] Starting MJPEG Stream Server on port %d...\n", config.server_port);
  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &stream_uri);
    httpd_register_uri_handler(stream_httpd, &capture_uri);
    Serial.println("[HTTP] Stream server started successfully at /stream");
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
 * Connects to local Wi-Fi with multi-network roaming and 2.4 GHz diagnostics.
 */
void setupWiFi() {
  Serial.println("\n[WiFi] ==========================================");
  Serial.println("[WiFi]   ESP32-CAM Wi-Fi Radio (2.4 GHz)");
  Serial.println("[WiFi] ==========================================");

  WiFi.disconnect(true);
  delay(100);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);
  WiFi.setSleep(false); // Critical on ESP32-CAM to prevent brownouts/dropped frames

  // 1. Diagnostic scan of nearby 2.4 GHz networks
  Serial.println("[WiFi] Scanning available 2.4 GHz Wi-Fi networks in range...");
  int n = WiFi.scanNetworks();
  if (n <= 0) {
    Serial.println("[WiFi] No networks found in scan! Ensure 2.4 GHz hotspot is active.");
  } else {
    Serial.printf("[WiFi] Found %d Wi-Fi networks in range:\n", n);
    for (int i = 0; i < n && i < 8; ++i) {
      Serial.printf("  (%d) %-20s [RSSI: %4d dBm, Ch: %2d]\n",
                    i + 1, WiFi.SSID(i).c_str(), WiFi.RSSI(i), WiFi.channel(i));
    }
  }

  // 2. Register multi-network APs
  wifiMulti.addAP(WIFI_SSID, WIFI_PASSWORD);
#ifdef WIFI_SSID_2
  if (strlen(WIFI_SSID_2) > 0) wifiMulti.addAP(WIFI_SSID_2, WIFI_PASSWORD_2);
#endif
#ifdef WIFI_SSID_3
  if (strlen(WIFI_SSID_3) > 0) wifiMulti.addAP(WIFI_SSID_3, WIFI_PASSWORD_3);
#endif

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  const int maxAttempts = 40;
  while (WiFi.status() != WL_CONNECTED && attempts < maxAttempts) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected successfully to hotspot!");
    Serial.print("[WiFi] Camera IP: ");
    Serial.println(WiFi.localIP());
    Serial.printf("[WiFi] Stream URL: http://%s:%d/stream\n", WiFi.localIP().toString().c_str(), STREAM_SERVER_PORT);
  } else {
    Serial.printf("\n[WiFi] Initial connection failed! Status: %s\n", getWiFiStatusString(WiFi.status()));
    Serial.println("[WiFi] Will auto-retry in loop...");
  }
}

/**
 * Reports camera heartbeat and stream URL to backend.
 */
void sendCameraHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
#ifdef BACKEND_BASE_URL
  String url = String(BACKEND_BASE_URL) + String(ENDPOINT_HEARTBEAT);
#else
  String protocol = USE_HTTPS ? "https://" : "http://";
  String url = protocol + String(BACKEND_HOST) + ":" + String(BACKEND_PORT) + String(ENDPOINT_HEARTBEAT);
#endif

  WiFiClientSecure secClient;
  WiFiClient plainClient;
  if (url.startsWith("https://")) {
    secClient.setInsecure();
    http.begin(secClient, url);
  } else {
    http.begin(plainClient, url);
  }
  http.setTimeout(3000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);

  String streamUrl = "http://" + WiFi.localIP().toString() + ":" + String(STREAM_SERVER_PORT) + "/stream";

  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["device_type"] = "esp32-cam";
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["status"] = "online";
  doc["ip_address"] = WiFi.localIP().toString();
  doc["stream_url"] = streamUrl;

  String payload;
  serializeJson(doc, payload);

  int httpCode = http.POST(payload);
  if (httpCode > 0) {
    Serial.printf("[Heartbeat] Camera heartbeat recorded (%d)\n", httpCode);
  }
  http.end();
}

unsigned long lastFrameUploadTime = 0;
#define FRAME_UPLOAD_INTERVAL_MS 1000 // Upload frame every 1s for seamless HTTPS web display

/**
 * Captures and uploads a live JPEG frame to Render over HTTPS.
 * Enables in-webpage camera display without mixed-content browser restrictions.
 */
void uploadCameraFrame() {
  if (WiFi.status() != WL_CONNECTED) return;

  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("[Camera] Capture failed for frame upload");
    return;
  }

  HTTPClient http;
#ifdef BACKEND_BASE_URL
  String url = String(BACKEND_BASE_URL) + "/api/camera/frame";
#else
  String protocol = USE_HTTPS ? "https://" : "http://";
  String url = protocol + String(BACKEND_HOST) + ":" + String(BACKEND_PORT) + "/api/camera/frame";
#endif

  WiFiClientSecure secClient;
  WiFiClient plainClient;
  if (url.startsWith("https://")) {
    secClient.setInsecure();
    http.begin(secClient, url);
  } else {
    http.begin(plainClient, url);
  }
  http.setTimeout(2500);
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);

  int httpCode = http.POST(fb->buf, fb->len);
  if (httpCode > 0) {
    Serial.printf("[Cloud Stream] Live frame uploaded (%u bytes, HTTP %d)\n", fb->len, httpCode);
  } else {
    Serial.printf("[Cloud Stream] Upload error: %s\n", http.errorToString(httpCode).c_str());
  }

  esp_camera_fb_return(fb);
  http.end();
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Disable brownout detector to prevent reboot spikes on mobile hotspot

  Serial.begin(115200);
  delay(500);

  Serial.println("\n==========================================");
  Serial.println("  GRAIN GUARDIAN - ESP32-CAM Node");
  Serial.println("  Hardware: AI-THINKER OV2640");
  Serial.println("==========================================");

  // Configure camera parameters
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // Frame size & PSRAM optimization
  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA; // 640x480
    config.jpeg_quality = 12;          // 0-63 (lower = higher quality)
    config.fb_count = 2;
    Serial.println("[Camera] PSRAM detected: using dual frame buffer (VGA 640x480).");
  } else {
    config.frame_size = FRAMESIZE_SVGA; // 800x600 fallback
    config.jpeg_quality = 14;
    config.fb_count = 1;
    Serial.println("[Camera] Warning: No PSRAM detected, using single frame buffer.");
  }

  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[Camera] Critical Error: esp_camera_init failed with error 0x%x\n", err);
    return;
  }
  Serial.println("[Camera] OV2640 camera hardware initialized successfully.");

  // Connect to Wi-Fi
  setupWiFi();

  // Start HTTP Streaming Server if connected
  if (WiFi.status() == WL_CONNECTED) {
    startCameraServer();
  }
}

void loop() {
  unsigned long currentMillis = millis();

  // Send heartbeat every 5 seconds to notify backend of camera availability and stream URL
  if (currentMillis - lastHeartbeatTime >= HEARTBEAT_INTERVAL_MS) {
    lastHeartbeatTime = currentMillis;
    if (WiFi.status() == WL_CONNECTED) {
      sendCameraHeartbeat();
    }
  }

  // Upload live JPEG frame every 1s to cloud relay (enables in-webpage viewing without mixed content errors)
  if (currentMillis - lastFrameUploadTime >= FRAME_UPLOAD_INTERVAL_MS) {
    lastFrameUploadTime = currentMillis;
    if (WiFi.status() == WL_CONNECTED) {
      uploadCameraFrame();
    }
  }

  // Maintain Wi-Fi connection
  if (WiFi.status() != WL_CONNECTED) {
    static unsigned long lastCamWifiRetry = 0;
    if (currentMillis - lastCamWifiRetry >= 8000) {
      lastCamWifiRetry = currentMillis;
      Serial.println("[WiFi] Reconnecting via WiFiMulti...");
      if (wifiMulti.run(4000) != WL_CONNECTED) {
        WiFi.disconnect(false);
        delay(50);
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
      }
    }
  } else if (stream_httpd == NULL) {
    startCameraServer();
  }

  delay(10);
}

