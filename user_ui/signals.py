from django.db.models.signals import post_save
from django.dispatch import receiver
from geopy.distance import geodesic
from .models import LiveLocation, Stop, ETARecord
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
            print(f"🚍 Bus {instance.bus} reached destination {stop.name} — Retraining model...")

            model, df = train_model()

            if model and not df.empty:
                latest = df.iloc[-1][["latitude", "longitude", "speed", "hour", "minute"]].values.reshape(1, -1)
                prediction = model.predict(latest)[0]

                ETARecord.objects.create(
                    bus=instance.bus,
                    predicted_eta=prediction
                )

                print(f"✅ ETA saved for Bus {instance.bus}: {prediction:.2f} minutes")

