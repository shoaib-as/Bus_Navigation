import pandas as pd
from geopy.distance import geodesic
from user_ui.models import LiveLocation, ArrivalLog

def build_training_dataset():
    rows = []

    logs = ArrivalLog.objects.all()
    for log in logs:
        loc = LiveLocation.objects.filter(bus=log.bus, timestamp__lte=log.arrival_time).order_by("-timestamp").first()
        if not loc:
            continue

        stop_coords = (log.stop.latitude, log.stop.longitude)
        bus_coords = (loc.latitude, loc.longitude)
        distance = geodesic(bus_coords, stop_coords).meters

        eta_minutes = (log.arrival_time - loc.timestamp).total_seconds() / 60.0

        rows.append({
            "distance_to_stop": distance,
            "speed": 0, 
            "hour": loc.timestamp.hour,
            "dayofweek": loc.timestamp.weekday(),
            "eta_minutes": eta_minutes
        })

    return pd.DataFrame(rows)
