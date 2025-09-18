# ml_model/feature_engineering.py

import numpy as np
import pandas as pd
from math import radians, cos, sin, atan2, sqrt
import requests

# Optional: Put your TomTom API key here (if traffic data needed)
TOMTOM_API_KEY = None  

# ----------------------------
# Geospatial Features
# ----------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance (km) between two points."""
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing (degrees) between two points."""
    dlon = radians(lon2 - lon1)
    lat1, lat2 = radians(lat1), radians(lat2)
    y = sin(dlon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    return (atan2(y, x) * 180 / np.pi + 360) % 360

def add_geospatial_features(df, stop_lat=None, stop_lon=None):
    """
    Add distance and bearing features.
    If stop_lat/lon provided: compute distance to stop, else relative distances.
    """
    if stop_lat is not None and stop_lon is not None:
        df["distance_to_stop"] = df.apply(
            lambda row: haversine_distance(row["latitude"], row["longitude"], stop_lat, stop_lon),
            axis=1
        )
        df["bearing_to_stop"] = df.apply(
            lambda row: bearing(row["latitude"], row["longitude"], stop_lat, stop_lon),
            axis=1
        )
    return df

# ----------------------------
# Temporal Features
# ----------------------------
def add_temporal_features(df, timestamp_col="timestamp"):
    """Add hour, minute, day, cyclical encoding."""
    df["hour"] = df[timestamp_col].dt.hour
    df["minute"] = df[timestamp_col].dt.minute
    df["day_of_week"] = df[timestamp_col].dt.weekday  # 0=Mon, 6=Sun
    
    # Cyclical encoding for hour
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    
    # Cyclical encoding for day of week
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    
    return df

# ----------------------------
# Traffic Features (Optional, using TomTom API)
# ----------------------------
def get_traffic_flow(lat, lon, radius=500):
    """Fetch traffic congestion level near bus location from TomTom API."""
    if not TOMTOM_API_KEY:
        return None
    
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    params = {"point": f"{lat},{lon}", "key": TOMTOM_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Congestion level = current speed / free flow speed
            current = data["flowSegmentData"]["currentSpeed"]
            free_flow = data["flowSegmentData"]["freeFlowSpeed"]
            return current / free_flow if free_flow > 0 else None
    except Exception as e:
        print("Traffic API error:", e)
    return None

def add_traffic_features(df):
    """Add traffic congestion feature (if API key is set)."""
    if not TOMTOM_API_KEY:
        df["traffic_congestion"] = np.nan
        return df

    df["traffic_congestion"] = df.apply(
        lambda row: get_traffic_flow(row["latitude"], row["longitude"]),
        axis=1
    )
    return df

# ----------------------------
# Main Pipeline
# ----------------------------
def enrich_features(df, stop_lat=None, stop_lon=None):
    """Run full feature engineering pipeline."""
    df = add_geospatial_features(df, stop_lat, stop_lon)
    df = add_temporal_features(df)
    df = add_traffic_features(df)
    return df
