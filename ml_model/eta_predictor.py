import joblib
import pandas as pd
from geopy.distance import geodesic
from user_ui.models import Bus, Stop, LiveLocation

model = joblib.load("ml_model/bus_eta_model.pkl")

def predict_eta(bus_id, stop_id):
    bus = Bus.objects.get(id=bus_id)
    stop = Stop.objects.get(id=stop_id)

    last_loc = LiveLocation.objects.filter(bus=bus).order_by("-timestamp").first()
    if not last_loc:
        return None

    distance = geodesic(
        (last_loc.latitude, last_loc.longitude),
        (stop.latitude, stop.longitude)
    ).meters

    features = pd.DataFrame([{
        "distance_to_stop": distance,
        "speed": 0,
        "hour": last_loc.timestamp.hour,
        "dayofweek": last_loc.timestamp.weekday()
    }])

    return round(model.predict(features)[0], 2)
