import pandas as pd
import numpy as np
from django.utils.timezone import now
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from .models import LiveLocation, Stop

def calculate_speed(lat1, lon1, lat2, lon2, t1, t2):
    from geopy.distance import geodesic
    distance = geodesic((lat1, lon1), (lat2, lon2)).km
    time_diff = (t2 - t1).total_seconds() / 3600
    if time_diff == 0:
        return 0
    return distance / time_diff

def prepare_dataset():
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
            data.append({
                "bus_id": loc.bus_id,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "speed": speed,
                "hour": loc.timestamp.hour,
                "minute": loc.timestamp.minute,
                "eta": np.random.randint(5, 30)
            })
        prev_point = loc

    return pd.DataFrame(data)

def train_model():
    df = prepare_dataset()
    if df.empty:
        print("Not enough data to train.")
        return None, None

    X = df[["latitude", "longitude", "speed", "hour", "minute"]]
    y = df["eta"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("MAE:", mean_absolute_error(y_test, y_pred))

    return model, df
