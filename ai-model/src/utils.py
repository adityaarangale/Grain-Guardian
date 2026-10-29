"""
Shared helper functions.
"""

import json
from datetime import datetime


def log_prediction(prediction: dict, filepath="../data/processed/prediction_log.jsonl"):
    """Append a prediction result to a log file, for later review/retraining."""
    entry = {**prediction, "timestamp": datetime.now().isoformat()}
    with open(filepath, "a") as f:
        f.write(json.dumps(entry) + "\n")


def validate_sensor_input(data: dict) -> bool:
    required_keys = ["grain_type", "temperature", "humidity", "gas_index", "moisture"]
    return all(k in data for k in required_keys)