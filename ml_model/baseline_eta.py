from user_ui.models import Bus, Stop, LiveLocation
from geopy.distance import geodesic
from django.utils.timezone import now

def estimate_eta(bus_id, stop_id):
    try:
        bus = Bus.objects.get(id=bus_id)
        stop = Stop.objects.get(id=stop_id)

        last_location = LiveLocation.objects.filter(bus=bus).order_by("-timestamp").first()
        if not last_location:
            return None

        distance = geodesic(
            (last_location.latitude, last_location.longitude),
            (stop.latitude, stop.longitude)
        ).meters

        last_two = LiveLocation.objects.filter(bus=bus).order_by("-timestamp")[:2]
        if len(last_two) < 2:
            return None

        loc1, loc2 = last_two[1], last_two[0]
        dist_m = geodesic(
            (loc1.latitude, loc1.longitude),
            (loc2.latitude, loc2.longitude)
        ).meters
        time_s = (loc2.timestamp - loc1.timestamp).total_seconds()
        
        if time_s <= 0:
            return None

        speed_kmh = (dist_m / time_s) * 3.6 
        if speed_kmh <= 0:
            return None

        eta_minutes = (distance / 1000) / (speed_kmh / 60.0)

        return round(eta_minutes, 2)

    except Exception as e:
        print("Error in estimate_eta:", e)
        return None
