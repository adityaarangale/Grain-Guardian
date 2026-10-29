"""
Data cleaning and feature engineering for sensor trend data.
"""

import pandas as pd


def load_raw_sensor_data(filepath: str) -> pd.DataFrame:
    """Load raw sensor CSV data."""
    return pd.read_csv(filepath)


def clean_sensor_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove nulls, duplicates, and obvious sensor error readings."""
    df = df.dropna()
    df = df.drop_duplicates()
    # Example: drop physically impossible readings
    df = df[(df["humidity"] >= 0) & (df["humidity"] <= 100)]
    df = df[(df["temperature"] >= -10) & (df["temperature"] <= 60)]
    return df


def add_trend_features(df: pd.DataFrame, group_col: str = "batch_id") -> pd.DataFrame:
    """Add rate-of-change features per batch, since trends matter more than single readings."""
    df = df.sort_values(["batch_id", "timestamp"])
    for col in ["temperature", "humidity", "gas_index", "moisture"]:
        df[f"{col}_delta"] = df.groupby(group_col)[col].diff().fillna(0)
    return df


def save_processed_data(df: pd.DataFrame, filepath: str):
    df.to_csv(filepath, index=False)