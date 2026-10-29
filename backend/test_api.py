import requests
import json
import os
import time

BASE_URL = "http://127.0.0.1:5000"

def test_api_endpoints():
    print("\n==========================================")
    print("  GRAIN GUARDIAN - BACKEND AUTH & API TESTER")
    print("==========================================\n")

    auth_headers = {}

    def safe_print_response(res_json):
        sanitized = dict(res_json)
        if "access_token" in sanitized:
            sanitized["access_token"] = "[REDACTED_JWT_TOKEN]"
        print(f"    Response: {json.dumps(sanitized, indent=2)}")

    # 1. Test GET / (Root Endpoint)
    print("[1] Testing GET / ...")
    res = requests.get(f"{BASE_URL}/")
    print(f"    Status: {res.status_code}")
    print(f"    Response: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 200

    # 2. Test POST /api/auth/signup
    test_email = f"operator_{int(time.time())}@facility.com"
    signup_payload = {
        "name": "Warehouse Manager",
        "email": test_email,
        "password": "SecurePassword123!"
    }
    print(f"\n[2] Testing POST /api/auth/signup ({test_email})...")
    res = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_payload)
    print(f"    Status: {res.status_code}")
    safe_print_response(res.json())
    assert res.status_code == 201
    assert "access_token" in res.json()

    # 2b. Test Duplicate Signup (Expect 400 Bad Request)
    print(f"\n[2b] Testing Duplicate Signup rejection for {test_email} (Expect 400)...")
    res_dup = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_payload)
    print(f"    Status: {res_dup.status_code} (Expected 400)")
    assert res_dup.status_code == 400
    assert res_dup.json().get("status") == "error"

    # 3. Test POST /api/auth/login
    print(f"\n[3] Testing POST /api/auth/login ({test_email})...")
    login_payload = {
        "email": test_email,
        "password": "SecurePassword123!"
    }
    res = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    print(f"    Status: {res.status_code}")
    safe_print_response(res.json())
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token is not None
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 3b. Test Login with incorrect password (Expect 401 Unauthorized)
    print(f"\n[3b] Testing login with wrong password (Expect 401)...")
    res_wrong = requests.post(f"{BASE_URL}/api/auth/login", json={"email": test_email, "password": "WrongPassword!"})
    print(f"    Status: {res_wrong.status_code} (Expected 401)")
    assert res_wrong.status_code == 401
    assert res_wrong.json().get("status") == "error"

    # 4. Test GET /api/auth/me (Protected Route)
    print("\n[4] Testing GET /api/auth/me (Protected Session Check)...")
    res = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
    print(f"    Status: {res.status_code}")
    safe_print_response(res.json())
    assert res.status_code == 200
    assert res.json()["user"]["email"] == test_email

    # 5. Test GET /api/storage-units
    print("\n[5] Testing GET /api/storage-units...")
    res = requests.get(f"{BASE_URL}/api/storage-units")
    print(f"    Status: {res.status_code}")
    print(f"    Response: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 200

    # 6. Test POST /api/sensor-data (ESP32 / Arduino Telemetry Upload)
    print("\n[6] Testing POST /api/sensor-data with final contract...")
    sensor_payload = {
        "storage_unit_id": 1,
        "grain_type": "wheat",
        "temperature": 28.5,
        "humidity": 62.0,
        "gas_index": 412,
        "moisture": 13.2
    }
    res = requests.post(f"{BASE_URL}/api/sensor-data", json=sensor_payload)
    print(f"    Status: {res.status_code}")
    print(f"    Response: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 201

    # 7. Test Protected GET /api/predict/1 without token (Expect 401)
    print("\n[7] Testing GET /api/predict/1 WITHOUT token (Expect 401 Unauthorized)...")
    res_unauth = requests.get(f"{BASE_URL}/api/predict/1")
    print(f"    Status: {res_unauth.status_code} (Expected 401)")
    assert res_unauth.status_code == 401

    # 8. Test Protected GET /api/predict/1 WITH Bearer token
    print("\n[8] Testing GET /api/predict/1 WITH Bearer Token...")
    res = requests.get(f"{BASE_URL}/api/predict/1", headers=auth_headers)
    print(f"    Status: {res.status_code}")
    print(f"    Response: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 200

    # 9. Test Protected POST /api/scan WITH Bearer Token
    print("\n[9] Testing POST /api/scan WITH Bearer Token...")
    dummy_img_path = os.path.join(os.path.dirname(__file__), "test_dummy.jpg")
    with open(dummy_img_path, "wb") as f:
        f.write(b"FFD8FFE000104A46494600010101006000600000FFD9")

    try:
        with open(dummy_img_path, "rb") as img_file:
            files = {"image": ("test_uv_scan.jpg", img_file, "image/jpeg")}
            data = {"storage_unit_id": 1}
            res = requests.post(f"{BASE_URL}/api/scan", data=data, files=files, headers=auth_headers)
            print(f"    Status: {res.status_code}")
            print(f"    Response: {json.dumps(res.json(), indent=2)}")
            assert res.status_code == 200
    finally:
        if os.path.exists(dummy_img_path):
            os.remove(dummy_img_path)

    # 10. Test Protected GET /api/dashboard/1 WITH Bearer Token
    print("\n[10] Testing GET /api/dashboard/1 WITH Bearer Token...")
    res = requests.get(f"{BASE_URL}/api/dashboard/1", headers=auth_headers)
    print(f"    Status: {res.status_code}")
    print(f"    Response: {json.dumps(res.json(), indent=2)}")
    assert res.status_code == 200

    # 11. Test GET /api/alerts and POST /api/alerts/<id>/acknowledge
    print("\n[11] Testing GET /api/alerts & Acknowledge...")
    res = requests.get(f"{BASE_URL}/api/alerts")
    print(f"    GET /api/alerts Status: {res.status_code}, count: {len(res.json().get('alerts', []))}")
    assert res.status_code == 200
    assert "alerts" in res.json()
    alerts = res.json()["alerts"]
    if alerts:
        test_alert_id = alerts[0]["id"]
        res_ack = requests.post(f"{BASE_URL}/api/alerts/{test_alert_id}/acknowledge")
        print(f"    POST /api/alerts/{test_alert_id}/acknowledge Status: {res_ack.status_code}")
        assert res_ack.status_code == 200

    # 12. Test GET /api/health
    print("\n[12] Testing GET /api/health...")
    res_health = requests.get(f"{BASE_URL}/api/health")
    print(f"    Status: {res_health.status_code}, body: {res_health.json()}")
    assert res_health.status_code == 200
    assert "simulate" in res_health.json()

    # 13. Test GET /api/readings?unit=&range=
    print("\n[13] Testing GET /api/readings?unit=1&range=24h...")
    res_readings = requests.get(f"{BASE_URL}/api/readings?unit=1&range=24h")
    print(f"    Status: {res_readings.status_code}, count: {res_readings.json().get('count')}")
    assert res_readings.status_code == 200
    assert "readings" in res_readings.json()

    # 14. Test GET /api/scans
    print("\n[14] Testing GET /api/scans...")
    res_scans = requests.get(f"{BASE_URL}/api/scans")
    print(f"    Status: {res_scans.status_code}, count: {res_scans.json().get('count')}")
    assert res_scans.status_code == 200
    assert "scans" in res_scans.json()

    # 15. Test POST /api/calibrate-baseline
    print("\n[15] Testing POST /api/calibrate-baseline...")
    res_cal = requests.post(f"{BASE_URL}/api/calibrate-baseline", json={"storage_unit_id": 1, "baseline": 85})
    print(f"    Status: {res_cal.status_code}, baseline: {res_cal.json().get('baseline')}")
    assert res_cal.status_code == 200

    print("\n==========================================")
    print("  ALL AUTH & API ENDPOINTS PASSED SUCCESSFULLY!")
    print("==========================================\n")
    return True

if __name__ == "__main__":
    test_api_endpoints()
