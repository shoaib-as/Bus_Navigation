from geopy.distance import geodesic
import numpy as np
import pandas as pd
from user_ui.models import LiveLocation, WeatherSnapshot, TrafficSnapshot

def time_of_day_sin_cos(dt):
    seconds = dt.hour*3600 + dt.minute*60 + dt.second
    sin = np.sin(2*np.pi*seconds/86400)
    cos = np.cos(2*np.pi*seconds/86400)
    return sin, cos

def extract_features_for_location(loc, stop):
    dist_m = geodesic((loc.latitude, loc.longitude), (stop.latitude, stop.longitude)).meters

    prev = LiveLocation.objects.filter(bus=loc.bus, timestamp__lt=loc.timestamp).order_by("-timestamp").first()
    speed_kmh = 0.0
    if prev:
        d_m = geodesic((prev.latitude, prev.longitude), (loc.latitude, loc.longitude)).meters
        dt_s = (loc.timestamp - prev.timestamp).total_seconds()
        if dt_s > 0:
            speed_kmh = (d_m / dt_s) * 3.6

    sin_t, cos_t = time_of_day_sin_cos(loc.timestamp)

    weather = WeatherSnapshot.objects.filter(
      timestamp__lte=loc.timestamp
    ).order_by("-timestamp").first()
    temp = getattr(weather, "temp_c", None)
    rain = getattr(weather, "precipitation", 0.0)

    traffic = TrafficSnapshot.objects.filter(
      timestamp__lte=loc.timestamp
    ).order_by("-timestamp").first()
    traffic_level = getattr(traffic, "traffic_level", 0.0)

    return {
      "distance_m": dist_m,
      "speed_kmh": speed_kmh,
      "time_sin": sin_t,
      "time_cos": cos_t,
      "temp_c": temp,
      "precip_mm": rain,
      "traffic_level": traffic_level
    }
