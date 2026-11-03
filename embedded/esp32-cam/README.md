# Grain Guardian — ESP32-CAM Firmware & Setup Specification

This directory contains the dedicated streaming and optical heartbeat firmware for the **ESP32-CAM (AI-Thinker OV2640)** module. The module provides a local MJPEG stream on port 81 and periodically registers its heartbeat and stream URL with the Render backend.

---

## 1. Hardware Pinout (AI-Thinker OV2640 Model)

```
        +-------------------+
        |  [ESP32-CAM Ant]  |
        |     [OV2640]      |
   5V --| 5V            GND |-- GND
  GND --| GND          IO12 |-- (NC)
 IO14 --| IO14         IO13 |-- (NC)
  IO2 --| IO2          IO15 |-- (NC)
  IO4 --| IO4 (Flash)  IO16 |-- (NC)
(U0R) --| U0R           IO0 |-- Bootloader Flash Jumper (Connect to GND to flash)
(U0T) --| U0T           VCC |-- 3.3V
        +-------------------+
```

### Camera Bus Pin Assignments

| Function | ESP32 GPIO Pin | Description |
| :--- | :--- | :--- |
| **PWDN** | `GPIO 32` | Power-down control |
| **RESET**| `-1` | Software reset |
| **XCLK** | `GPIO 0` | Master external clock (20 MHz) |
| **SIOD** | `GPIO 26` | I2C SCCB Data |
| **SIOC** | `GPIO 27` | I2C SCCB Clock |
| **Y9–Y2**| `35, 34, 39, 36, 21, 19, 18, 5` | Parallel 8-bit image data bus |
| **VSYNC**| `GPIO 25` | Vertical Sync |
| **HREF** | `GPIO 23` | Horizontal Reference |
| **PCLK** | `GPIO 22` | Pixel Clock |

---

## 2. Flashing the ESP32-CAM Module

The standard ESP32-CAM lacks an onboard USB-UART chip. To flash:
1. Connect an external **FTDI / CP2102 USB-to-Serial Adapter**:
   - `FTDI 5V` &rarr; `ESP32-CAM 5V` (or VIN)
   - `FTDI GND` &rarr; `ESP32-CAM GND`
   - `FTDI TX` &rarr; `ESP32-CAM U0R (GPIO 3)`
   - `FTDI RX` &rarr; `ESP32-CAM U0T (GPIO 1)`
2. **Flash Mode Jumper**: Connect `GPIO 0` to `GND`.
3. Press the onboard **RST** button to enter download mode.
4. Upload firmware via PlatformIO or Arduino IDE (Board: **"AI Thinker ESP32-CAM"**).
5. After upload completes:
   - **Disconnect `GPIO 0` from `GND`**.
   - Press **RST** to boot the camera into run mode.
   - Open Serial Monitor at **115200 Baud** to observe the assigned local IP.

---

## 3. Network Architecture & Local Wi-Fi Streaming

* **Port 81 Stream**: The camera hosts a lightweight MJPEG server on `http://<ESP32_CAM_IP>:81/stream`.
* **Single Snapshot Endpoint**: `http://<ESP32_CAM_IP>:81/capture` returns a single JPEG frame.
* **LAN Constraint**:
  - The browser on your laptop or phone must be on the **same Wi-Fi network** to view the live video stream from `http://192.168.x.x:81/stream`.
  - The Render cloud backend does not proxy continuous video streams to prevent bandwidth bottlenecks and serverless timeouts.
  - For remote viewing outside your local network, deploy a secure tunnel (e.g. Cloudflare Tunnel or ngrok) pointing to `<ESP32_CAM_IP>:81`.

