from django.db.models.signals import post_save
from django.dispatch import receiver
from geopy.distance import geodesic
from django.utils import timezone
from .models import LiveLocation, Stop, ArrivalLog, ETARecord
from user_ui.ml_pipeline import train_model  # or enqueue training task

DESTINATION_THRESHOLD_M = 60  # meters, tune as needed
DEDUPE_WINDOW_SECONDS = 120    # avoid duplicate arrival logs within this window

@receiver(post_save, sender=LiveLocation)
def check_destination_and_log_arrival(sender, instance, created, **kwargs):
    # only consider newly created LiveLocation entries
    if not created:
        return

    # iterate stops (you can filter stops per route later)
    stops = Stop.objects.all()
    for stop in stops:
        try:
            dist_m = geodesic(
                (instance.latitude, instance.longitude),
                (stop.latitude, stop.longitude)
            ).meters
        except Exception:
            continue

        if dist_m <= DESTINATION_THRESHOLD_M:
            # dedupe: check if we already logged arrival for same bus-stop recently
            recent_cutoff = timezone.now() - timezone.timedelta(seconds=DEDUPE_WINDOW_SECONDS)
            exists = ArrivalLog.objects.filter(
                bus=instance.bus, stop=stop, arrival_time__gte=recent_cutoff
            ).exists()
            if exists:
                return

            # create arrival log
            ArrivalLog.objects.create(bus=instance.bus, stop=stop, arrival_time=instance.timestamp)

            try:
                model, df = train_model() 
            except Exception as e:
                print("Training triggered but failed:", e)

            break
