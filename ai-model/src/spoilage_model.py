"""
Spoilage prediction model: trend-based risk classification and safe-days estimation.
"""

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from grain_profiles import get_profile

FEATURES = [
    "temperature", "humidity", "gas_index", "moisture",
    "temperature_delta", "humidity_delta", "gas_index_delta", "moisture_delta",
]

RISK_LABELS = ["Safe", "Medium", "High", "Critical"]


def train_model(df, target_col="risk_level", save_path="../models/spoilage_model.pkl"):
    X = df[FEATURES]
    y = df[target_col]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=150, random_state=42)
    model.fit(X_train, y_train)

    print("Test accuracy:", model.score(X_test, y_test))
    joblib.dump(model, save_path)
    return model


def load_model(path="../models/spoilage_model.pkl"):
    return joblib.load(path)


def predict(model, sensor_reading: dict) -> dict:
    """
    sensor_reading: dict with keys matching FEATURES (deltas can default to 0
    for a first-ever reading with no history yet)
    """
    grain_profile = get_profile(sensor_reading.get("grain_type", "wheat"))

    row = [[sensor_reading.get(f, 0) for f in FEATURES]]
    risk_idx = model.predict(row)[0]
    probability = max(model.predict_proba(row)[0])

    risk_level = RISK_LABELS[risk_idx] if isinstance(risk_idx, int) else risk_idx

    # simple safe-days heuristic — refine this once real data is available
    safe_days_map = {"Safe": 20, "Medium": 8, "High": 3, "Critical": 0}
    safe_days = safe_days_map.get(risk_level, 5)

    recommendations = {
        "Safe": "No action needed.",
        "Medium": "Monitor closely, re-check in 3 days.",
        "High": "Sell soon or arrange transfer.",
        "Critical": "Immediate action required — inspect and possibly discard.",
    }

    return {
        "risk_level": risk_level,
        "spoilage_probability": round(float(probability), 2),
        "safe_days_remaining": safe_days,
        "recommendation": recommendations.get(risk_level, "Monitor storage conditions."),
    }