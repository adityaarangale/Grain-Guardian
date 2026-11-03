import unittest
import json
import time
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, RUNTIME_STATE, ESP32_OFFLINE_THRESHOLD_SEC, CAM_OFFLINE_THRESHOLD_SEC

class HardwareApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("status", data)
        self.assertIn("database", data)
        self.assertIn("esp32_devkit_online", data)
        self.assertIn("esp32_cam_online", data)

    def test_device_heartbeat_devkit_and_cam(self):
        # 1. DevKit Heartbeat
        res_dev = self.client.post("/api/device/heartbeat", json={
            "device_id": "esp32-devkit",
            "ip_address": "192.168.1.105",
            "firmware_version": "1.2.0",
            "status": "online"
        })
        self.assertEqual(res_dev.status_code, 200)
        self.assertEqual(res_dev.get_json()["device"], "esp32-devkit")

        # 2. Camera Heartbeat
        res_cam = self.client.post("/api/device/heartbeat", json={
            "device_id": "esp32-cam",
            "ip_address": "192.168.1.106",
            "stream_url": "http://192.168.1.106:81/stream",
            "firmware_version": "1.0.1",
            "status": "online"
        })
        self.assertEqual(res_cam.status_code, 200)
        self.assertEqual(res_cam.get_json()["device"], "esp32-cam")

        # 3. Check Camera Status
        res_cam_stat = self.client.get("/api/camera/status")
        self.assertEqual(res_cam_stat.status_code, 200)
        cam_data = res_cam_stat.get_json()
        self.assertTrue(cam_data["online"])
        self.assertEqual(cam_data["stream_url"], "http://192.168.1.106:81/stream")

    def test_sensor_data_ingestion_and_dashboard(self):
        # Post realistic sensor telemetry including raw ADCs
        telemetry = {
            "storage_unit_id": 1,
            "grain_type": "wheat",
            "temperature": 24.5,
            "humidity": 58.0,
            "gas_index": 95,
            "moisture": 12.8,
            "raw_moisture": 2680,
            "mq2_raw": 140,
            "is_calibrated": True
        }
        res_post = self.client.post("/api/sensor-data", json=telemetry)
        self.assertEqual(res_post.status_code, 201)

        # Retrieve consolidated dashboard
        res_dash = self.client.get("/api/dashboard/1")
        self.assertEqual(res_dash.status_code, 200)
        dash = res_dash.get_json()

        self.assertIn("latest_sensor_reading", dash)
        reading = dash["latest_sensor_reading"]
        self.assertEqual(reading["temperature"], 24.5)
        self.assertEqual(reading["humidity"], 58.0)
        self.assertEqual(reading["raw_moisture"], 2680)
        self.assertEqual(reading["mq2_raw"], 140)
        self.assertEqual(reading["co2_status"], "CO2 sensor not installed")

        self.assertIn("devices", dash)
        self.assertTrue(dash["devices"]["esp32_devkit"]["online"])

        self.assertIn("relays", dash)
        self.assertIn("risk", dash)
        self.assertEqual(dash["risk"]["risk_level"], "Safe")
        self.assertFalse(dash["risk"]["is_provisional"])

    def test_relay_command_and_mutual_exclusion(self):
        # 1. Ensure DevKit is registered as online
        self.client.post("/api/device/heartbeat", json={"device_id": "esp32-devkit"})

        # 2. Dispatch UV ON command (Must automatically set White OFF)
        res_cmd = self.client.post("/api/device/command", json={"target": "uv", "state": "on"})
        self.assertEqual(res_cmd.status_code, 202)
        cmd_data = res_cmd.get_json()
        cmd_id = cmd_data["command_id"]
        self.assertTrue(cmd_data["target_states"]["uv_light"])
        self.assertFalse(cmd_data["target_states"]["white_light"])

        # 3. ESP32 DevKit polls command
        res_poll = self.client.get("/api/device/command")
        self.assertEqual(res_poll.status_code, 200)
        poll_data = res_poll.get_json()
        self.assertTrue(poll_data["has_command"])
        self.assertEqual(poll_data["command"]["command_id"], cmd_id)

        # 4. ESP32 DevKit confirms execution
        res_ack = self.client.post("/api/device/command-result", json={
            "command_id": cmd_id,
            "status": "acknowledged",
            "white_light": False,
            "uv_light": True
        })
        self.assertEqual(res_ack.status_code, 200)
        ack_data = res_ack.get_json()
        self.assertTrue(ack_data["actual_relay_state"]["uv_light"])
        self.assertFalse(ack_data["actual_relay_state"]["white_light"])

        # 5. Check dashboard reflects confirmed relay states
        res_dash = self.client.get("/api/dashboard")
        self.assertEqual(res_dash.status_code, 200)
        self.assertTrue(res_dash.get_json()["relays"]["uv_light"])
        self.assertFalse(res_dash.get_json()["relays"]["white_light"])

        # 6. Test Safety Override: if hardware mistakenly reports both ON, server forces White OFF
        res_override = self.client.post("/api/device/command-result", json={
            "command_id": "test_both_on",
            "status": "acknowledged",
            "white_light": True,
            "uv_light": True
        })
        self.assertEqual(res_override.status_code, 200)
        # Safety override ensures both can NEVER be true
        self.assertFalse(res_override.get_json()["actual_relay_state"]["white_light"])

if __name__ == "__main__":
    unittest.main()

