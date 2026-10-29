import os
import sys
import json

# Ensure ai-model root directory is in sys.path
AI_MODEL_ROOT = os.path.abspath(os.path.dirname(__file__))
if AI_MODEL_ROOT not in sys.path:
    sys.path.append(AI_MODEL_ROOT)

from api.predict import predict_spoilage, predict_contamination

def run_tests():
    print("==========================================")
    print("  AI-MODEL STANDALONE PREDICTION TESTER")
    print("==========================================\n")

    # 1. Test Spoilage Risk Model Prediction
    sample_spoilage_input = {
        "grain_type": "maize",
        "temperature": 30.0,
        "humidity": 70.0,
        "gas_index": 180,
        "moisture": 14.5
    }

    print("[1] Testing predict_spoilage() with sample input:")
    print(f"    Input: {json.dumps(sample_spoilage_input)}")
    
    spoilage_output = predict_spoilage(sample_spoilage_input)
    print("\n    Output:")
    print(json.dumps(spoilage_output, indent=2))

    # Verify JSON Schema
    expected_spoilage_keys = {"risk_level", "spoilage_probability", "safe_days_remaining", "recommendation"}
    assert expected_spoilage_keys.issubset(set(spoilage_output.keys())), "Spoilage prediction output schema mismatch!"
    print("    -> Spoilage JSON schema contract verified!\n")

    # 2. Test Contamination Classifier
    print("[2] Testing predict_contamination() with sample input image:")
    sample_img_path = os.path.join(AI_MODEL_ROOT, "data", "raw", "sample_test_scan.jpg")

    # Create synthetic placeholder test image if missing
    if not os.path.exists(sample_img_path):
        os.makedirs(os.path.dirname(sample_img_path), exist_ok=True)
        with open(sample_img_path, "wb") as f:
            f.write(b"FFD8FFE000104A46494600010101006000600000FFD9")
        print(f"    Note: Created dummy image at {sample_img_path} for testing.")

    contamination_output = predict_contamination(sample_img_path)
    print("\n    Output:")
    print(json.dumps(contamination_output, indent=2))

    # Verify JSON Schema
    expected_contamination_keys = {"contamination_risk", "confidence"}
    assert set(contamination_output.keys()) == expected_contamination_keys, "Contamination prediction output schema mismatch!"
    print("    -> Contamination JSON schema contract verified!\n")

    print("==========================================")
    print("  ALL AI-MODEL PREDICTION TESTS PASSED!")
    print("==========================================\n")

if __name__ == "__main__":
    run_tests()
