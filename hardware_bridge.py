#!/usr/bin/env python3
"""
Grain Guardian - Hardware Bridge
Connects physical Arduino/ESP32 sensor line or generates simulated telemetry.

Settings are read from .env:
  SERIAL_PORT : Serial COM port (e.g. COM3, COM4, /dev/ttyUSB0)
  BAUD        : Baud rate (default: 9600)
  API_URL     : Backend API URL (default: http://localhost:5000)
  SIMULATE    : 1 for simulation mode, 0 for physical Arduino serial line
"""

import os
import sys
import time
import json
import random
import io
import argparse

try:
    import requests
except ImportError:
    print("[Error] 'requests' library not found. Run: pip install requests")
    sys.exit(1)

# OpenCV and NumPy for realistic simulated UV scan frame generation
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# Try importing pyserial for physical hardware mode
try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


def load_env(env_path=None):
    """Load configuration variables from .env file into os.environ if not already set."""
    candidates = [
        env_path,
        ".env",
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(__file__), "backend", ".env")
    ]
    for p in candidates:
        if p and os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k not in os.environ:
                                os.environ[k] = v
                break
            except Exception as e:
                print(f"[Warning] Error parsing {p}: {e}")


def get_config():
    """Retrieve bridge settings from environment / .env."""
    load_env()
    serial_port = os.getenv("SERIAL_PORT", "COM3")
    try:
        baud = int(os.getenv("BAUD", "9600"))
    except ValueError:
        baud = 9600
    api_url = os.getenv("API_URL", "http://localhost:5000").rstrip("/")
    simulate_raw = os.getenv("SIMULATE", "1").strip().lower()
    simulate = 1 if simulate_raw in ("1", "true", "yes", "simulation") else 0

    return {
        "SERIAL_PORT": serial_port,
        "BAUD": baud,
        "API_URL": api_url,
        "SIMULATE": simulate
    }


def generate_fake_scan_image():
    """
    Generates a realistic 640x480 365nm UV darkfield capture frame
    with simulated optical bright greenish-yellow fluorescence (BGYF) spots.
    Returns JPEG image bytes.
    """
    if not HAS_CV2:
        # Minimal valid 1x1 JPEG bytes if OpenCV is unavailable
        return b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x60\x00\x60\x00\x00\xFF\xDB\x00C\x00\xFF\xD9"

    width, height = 640, 480
    # Deep dark purple UV illumination background
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (35, 10, 25)

    # Add realistic grain sample texture noise
    noise = np.random.normal(0, 10, (height, width, 3)).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Vignette circular mask simulating camera lens chamber
    Y, X = np.ogrid[:height, :width]
    dist_from_center = np.sqrt((X - width / 2)**2 + (Y - height / 2)**2)
    max_radius = min(width, height) * 0.48
    chamber_mask = dist_from_center <= max_radius
    img[~chamber_mask] = (10, 5, 8)

    # Draw simulated grain contours
    for _ in range(35):
        gx = random.randint(140, 500)
        gy = random.randint(100, 380)
        axes = (random.randint(16, 28), random.randint(10, 18))
        angle = random.randint(0, 180)
        cv2.ellipse(img, (gx, gy), axes, angle, 0, 360, (55, 30, 45), -1)

    # 15% probability of positive fluorescence spot
    has_positive_spot = random.random() < 0.25
    if has_positive_spot:
        spot_count = random.randint(3, 7)
        for _ in range(spot_count):
            fx = random.randint(180, 460)
            fy = random.randint(140, 340)
            fr = random.randint(8, 16)
            cv2.circle(img, (fx, fy), fr, (30, 240, 215), -1)  # Vivid yellow-green
            cv2.circle(img, (fx, fy), fr + 5, (15, 180, 160), 2)
    else:
        # Baseline minimal fluorescence trace
        for _ in range(random.randint(1, 3)):
            fx = random.randint(200, 440)
            fy = random.randint(160, 320)
            fr = random.randint(3, 5)
            cv2.circle(img, (fx, fy), fr, (25, 210, 190), -1)

    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return buf.tobytes()


class BridgeState:
    """Maintains realistic drifting telemetry state for storage units."""
    def __init__(self):
        self.units = [
            {"id": 1, "grain": "wheat", "temp": 26.2, "hum": 61.5, "gas": 125, "moist": 13.4},
            {"id": 2, "grain": "maize", "temp": 27.5, "hum": 64.0, "gas": 140, "moist": 14.1},
            {"id": 3, "grain": "groundnut", "temp": 23.8, "hum": 59.2, "gas": 112, "moist": 7.8},
            {"id": 4, "grain": "maize", "temp": 28.0, "hum": 66.5, "gas": 155, "moist": 14.8}
        ]
        self.cycle_count = 0

    def step_telemetry(self, unit_id=1):
        unit = next((u for u in self.units if u["id"] == unit_id), self.units[0])
        # Random walk drift with realistic bounds
        unit["temp"] = round(max(20.0, min(34.0, unit["temp"] + random.uniform(-0.15, 0.15))), 1)
        unit["hum"] = round(max(50.0, min(80.0, unit["hum"] + random.uniform(-0.25, 0.25))), 1)
        unit["gas"] = int(max(80, min(260, unit["gas"] + random.randint(-4, 4))))
        unit["moist"] = round(max(7.0, min(17.5, unit["moist"] + random.uniform(-0.08, 0.08))), 1)
        return {
            "storage_unit_id": unit["id"],
            "grain_type": unit["grain"],
            "temperature": unit["temp"],
            "humidity": unit["hum"],
            "gas_index": unit["gas"],
            "moisture": unit["moist"]
        }


def run_simulation_mode(config, loop_delay=5.0, max_iterations=None):
    """
    SIMULATE=1: Generates realistic continuous readings and periodic UV scan uploads.
    """
    print("\n=======================================================")
    print("  GRAIN GUARDIAN - HARDWARE BRIDGE (SIMULATION MODE)   ")
    print("=======================================================")
    print(f"  * Mode        : SIMULATE = 1 (Synthetic Telemetry)")
    print(f"  * Target API  : {config['API_URL']}/api/sensor-data")
    print(f"  * Loop Delay  : {loop_delay}s")
    print("  * Contract    : {\"storage_unit_id\":1,\"grain_type\":\"wheat\",\"temperature\":28.5,\"humidity\":62.0,\"gas_index\":412,\"moisture\":13.2}")
    print("=======================================================\n")

    state = BridgeState()
    iteration = 0

    while True:
        iteration += 1
        # Alternate through units
        for unit in state.units:
            payload = state.step_telemetry(unit["id"])
            try:
                res = requests.post(
                    f"{config['API_URL']}/api/sensor-data",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=3.0
                )
                if res.status_code == 201:
                    print(f"[{time.strftime('%H:%M:%S')}] [Unit #{payload['storage_unit_id']} - {payload['grain_type'].capitalize()}] "
                          f"Temp: {payload['temperature']}°C | Hum: {payload['humidity']}% | Gas: {payload['gas_index']} | Moist: {payload['moisture']}% -> HTTP 201 (OK)")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] [POST Failed] HTTP {res.status_code}: {res.text}")
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] [API Connect Error]: {e}")

        # Every 6 iterations (~30s), post a simulated UV scan sample for Unit 1
        if iteration % 6 == 0:
            print(f"[{time.strftime('%H:%M:%S')}] [UV Scan Engine] Generating synthetic 365nm fluorescence frame for Unit #1...")
            img_bytes = generate_fake_scan_image()
            try:
                files = {"image": ("simulated_uv_scan.jpg", img_bytes, "image/jpeg")}
                data = {"storage_unit_id": 1}
                scan_res = requests.post(f"{config['API_URL']}/api/scan", data=data, files=files, timeout=5.0)
                if scan_res.status_code == 200:
                    scan_json = scan_res.json()
                    print(f"  -> UV Scan Captured! Status: {scan_json.get('screening_status', 'Clear')}, Area: {scan_json.get('fluorescence_area_pct', 0.0)}%")
            except Exception as e:
                print(f"  -> UV Scan Upload Error: {e}")

        if max_iterations and iteration >= max_iterations:
            break

        time.sleep(loop_delay)


def run_hardware_mode(config):
    """
    SIMULATE=0: Connects to Arduino / ESP32 serial COM port and parses JSON lines.
    """
    print("\n=======================================================")
    print("  GRAIN GUARDIAN - HARDWARE BRIDGE (PHYSICAL SERIAL)  ")
    print("=======================================================")
    print(f"  * Mode        : SIMULATE = 0 (Physical Hardware)")
    print(f"  * Serial Port : {config['SERIAL_PORT']}")
    print(f"  * Baud Rate   : {config['BAUD']}")
    print(f"  * Target API  : {config['API_URL']}/api/sensor-data")
    print("=======================================================\n")

    if not HAS_SERIAL:
        print("[Fatal Error] 'pyserial' package is not installed.")
        print("To read physical hardware serial ports, install pyserial:")
        print("    pip install pyserial")
        sys.exit(1)

    while True:
        try:
            print(f"[*] Opening serial connection to {config['SERIAL_PORT']} at {config['BAUD']} baud...")
            ser = serial.Serial(config["SERIAL_PORT"], config["BAUD"], timeout=2.0)
            print(f"[+] Connected to {config['SERIAL_PORT']}. Awaiting incoming Arduino telemetry frames...\n")

            while True:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                # Filter debug / comment lines
                if not line.startswith("{") or not line.endswith("}"):
                    print(f"  [Arduino Serial Log] {line}")
                    continue

                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    print(f"  [Warning] Incomplete JSON received: {line}")
                    continue

                # Ensure final sensor contract fields
                required_fields = ["storage_unit_id", "grain_type", "temperature", "humidity", "gas_index", "moisture"]
                missing = [f for f in required_fields if f not in payload]
                if missing:
                    print(f"  [Warning] Missing fields {missing} in payload: {line}")
                    continue

                try:
                    res = requests.post(
                        f"{config['API_URL']}/api/sensor-data",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=3.0
                    )
                    if res.status_code == 201:
                        print(f"[{time.strftime('%H:%M:%S')}] [Physical Telemetry] Unit #{payload['storage_unit_id']} ({payload['grain_type']}) "
                              f"Temp: {payload['temperature']}°C | Hum: {payload['humidity']}% | Gas: {payload['gas_index']} | Moist: {payload['moisture']}% -> Recorded")
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] [API Error] HTTP {res.status_code}: {res.text}")
                except Exception as e:
                    print(f"[{time.strftime('%H:%M:%S')}] [API Post Error]: {e}")

        except serial.SerialException as se:
            print(f"[Serial Error] Could not connect to {config['SERIAL_PORT']}: {se}")
            print("[*] Retrying connection in 5 seconds... (Ensure Arduino is plugged in and port is set in .env)")
            time.sleep(5.0)
        except KeyboardInterrupt:
            print("\n[Bridge] Stopped by user.")
            break


def main():
    parser = argparse.ArgumentParser(description="Grain Guardian Hardware Bridge")
    parser.add_argument("--simulate", type=int, choices=[0, 1], help="Override SIMULATE mode (1=Simulate, 0=Hardware)")
    parser.add_argument("--port", type=str, help="Override SERIAL_PORT (e.g. COM3, COM4, /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, help="Override serial BAUD rate (default: 9600)")
    parser.add_argument("--url", type=str, help="Override backend API URL (default: http://localhost:5000)")
    parser.add_argument("--once", action="store_true", help="Run a single iteration and exit (for testing)")
    args = parser.parse_args()

    config = get_config()
    if args.simulate is not None:
        config["SIMULATE"] = args.simulate
    if args.port:
        config["SERIAL_PORT"] = args.port
    if args.baud:
        config["BAUD"] = args.baud
    if args.url:
        config["API_URL"] = args.url.rstrip("/")

    try:
        if config["SIMULATE"] == 1:
            run_simulation_mode(config, max_iterations=1 if args.once else None)
        else:
            run_hardware_mode(config)
    except KeyboardInterrupt:
        print("\n[Bridge] Shutting down cleanly.")


if __name__ == "__main__":
    main()
