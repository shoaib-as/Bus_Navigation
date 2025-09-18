import pandas as pd
import numpy as np
from django.utils.timezone import now
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib
from threading import Thread
from .models import LiveLocation, ArrivalLog
from geopy.distance import geodesic

from ml_model.feature_engineering import enrich_features  

MODEL_PATH = "ml_model/models/eta_xgb.pkl"
LATEST_TRAINED_TIMESTAMP = None  # Track latest trained timestamp

# ----------------------------
# Helper functions
# ----------------------------
def calculate_speed(lat1, lon1, lat2, lon2, t1, t2):
    distance = geodesic((lat1, lon1), (lat2, lon2)).km
    time_diff = (t2 - t1).total_seconds() / 3600
    if time_diff == 0:
        return 0
    return distance / time_diff

def get_eta_from_logs(bus_id, timestamp, stop_lat, stop_lon):
    arrival = (
        ArrivalLog.objects
        .filter(bus_id=bus_id, created_at__gte=timestamp)
        .order_by("created_at")
        .first()
    )
    if arrival:
        return (arrival.created_at - timestamp).total_seconds() / 60.0
    return None

# ----------------------------
# Dataset Preparation
# ----------------------------
def prepare_dataset(stop_lat=None, stop_lon=None):
    data = []
    live_locations = LiveLocation.objects.select_related("bus").order_by("timestamp")
    prev_point = None
    for loc in live_locations:
        if prev_point and prev_point.bus_id == loc.bus_id:
            speed = calculate_speed(
                prev_point.latitude, prev_point.longitude,
                loc.latitude, loc.longitude,
                prev_point.timestamp, loc.timestamp
            )

            eta = get_eta_from_logs(loc.bus_id, loc.timestamp, stop_lat, stop_lon)
            if eta is None:
                continue

            data.append({
                "bus_id": loc.bus_id,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "speed": speed,
                "timestamp": loc.timestamp,
                "eta": eta
            })
        prev_point = loc

    df = pd.DataFrame(data)
    if not df.empty:
        df = enrich_features(df, stop_lat=stop_lat, stop_lon=stop_lon)
    return df

# ----------------------------
# Training
# ----------------------------
def train_model(stop_lat=None, stop_lon=None):
    global LATEST_TRAINED_TIMESTAMP

    df = prepare_dataset(stop_lat, stop_lon)
    if df.empty:
        print("Not enough data to train.")
        return None, None

    feature_cols = [col for col in df.columns if col not in ["bus_id", "timestamp", "eta"]]
    X = df[feature_cols]
    y = df["eta"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=8,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        tree_method="hist"
    )

    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

    y_pred = model.predict(X_test)
    print("Validation MAE:", mean_absolute_error(y_test, y_pred))

    joblib.dump(model, MODEL_PATH)
    print(f"✅ Model saved at {MODEL_PATH}")

    # Update the last trained timestamp
    LATEST_TRAINED_TIMESTAMP = df['timestamp'].max()

    return model, df

# ----------------------------
# Auto-train in background
# ----------------------------
def auto_train_if_needed(stop_lat=None, stop_lon=None):
    global LATEST_TRAINED_TIMESTAMP
    latest_live = LiveLocation.objects.order_by('-timestamp').first()
    if latest_live and (LATEST_TRAINED_TIMESTAMP is None or latest_live.timestamp > LATEST_TRAINED_TIMESTAMP):
        # New data exists → train in background thread
        Thread(target=train_model, args=(stop_lat, stop_lon), daemon=True).start()

# ----------------------------
# Prediction
# ----------------------------
def predict_eta(lat, lon, speed, timestamp, stop_lat=None, stop_lon=None):
    auto_train_if_needed(stop_lat, stop_lon)  # Trigger auto-training if new data exists

    try:
        model = joblib.load(MODEL_PATH)
    except:
        print("Model not trained yet.")
        return None

    df = pd.DataFrame([{
        "latitude": lat,
        "longitude": lon,
        "speed": speed,
        "timestamp": timestamp
    }])

    df = enrich_features(df, stop_lat=stop_lat, stop_lon=stop_lon)

    feature_cols = [col for col in df.columns if col not in ["bus_id", "timestamp", "eta"]]
    return model.predict(df[feature_cols])[0]
