#ifndef CAMERA_CONFIG_H_
#define CAMERA_CONFIG_H_

// ==========================================
// 1. Network & Backend REST API Configuration
// ==========================================
// Production Render URL
#define BACKEND_BASE_URL "https://grain-guardian-api.onrender.com"
#define BACKEND_HOST "grain-guardian-api.onrender.com"
#define BACKEND_PORT 443
#define USE_HTTPS true

#define ENDPOINT_HEARTBEAT "/api/device/heartbeat"

// Device Identity
#define DEVICE_ID "esp32-cam"
#define FIRMWARE_VERSION "1.1.0"
#define DEVICE_TOKEN "grain-guardian-device-token-2026"

// Local Streaming Port (Standard ESP32-CAM stream port)
#define STREAM_SERVER_PORT 81

// Timing
#define HEARTBEAT_INTERVAL_MS 5000

#endif // CAMERA_CONFIG_H_

