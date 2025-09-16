from django.db.models.signals import post_save
from django.dispatch import receiver
from geopy.distance import geodesic
from .models import LiveLocation, Stop
from .ml_pipeline import train_model

@receiver(post_save, sender=LiveLocation)
def check_destination_and_train(sender, instance, **kwargs):
    destinations = Stop.objects.filter(is_destination=True)

    for stop in destinations:
        distance = geodesic(
            (instance.latitude, instance.longitude),
            (stop.latitude, stop.longitude)
        ).meters

        if distance < 100:
            print(f"Bus {instance.bus} reached destination {stop.name} ✅ Training model...")
            train_model()
            break
