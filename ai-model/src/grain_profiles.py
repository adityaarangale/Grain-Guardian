"""
Grain-specific threshold profiles.
Used by the spoilage prediction model and to schedule UV scan frequency.
"""

GRAIN_PROFILES = {
    "wheat": {
        "safe_moisture_max": 13.0,      # percent
        "gas_index_alert_threshold": 250,
        "aflatoxin_risk": "low",
        "scan_frequency_days": 14,
    },
    "rice": {
        "safe_moisture_max": 14.0,
        "gas_index_alert_threshold": 250,
        "aflatoxin_risk": "low",
        "scan_frequency_days": 14,
    },
    "maize": {
        "safe_moisture_max": 13.5,
        "gas_index_alert_threshold": 200,
        "aflatoxin_risk": "high",
        "scan_frequency_days": 5,
    },
    "groundnut": {
        "safe_moisture_max": 7.0,
        "gas_index_alert_threshold": 180,
        "aflatoxin_risk": "high",
        "scan_frequency_days": 5,
    },
    "pulses": {
        "safe_moisture_max": 12.0,
        "gas_index_alert_threshold": 260,
        "aflatoxin_risk": "medium",
        "scan_frequency_days": 10,
    },
}


def get_profile(grain_type: str) -> dict:
    """Return the threshold profile for a given grain type, default to wheat if unknown."""
    return GRAIN_PROFILES.get(grain_type.lower(), GRAIN_PROFILES["wheat"])