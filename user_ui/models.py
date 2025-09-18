from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100)
    bio = models.TextField(max_length=255, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username



class Bus(models.Model):
    bus_number = models.CharField(max_length=20, unique=True)
    route_name = models.CharField(max_length=100)
    latitude = models.FloatField() 
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.bus_number} - {self.route_name}"


class Stop(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name


class LiveLocation(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bus.bus_number} @ {self.timestamp}"


class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bus = models.OneToOneField(Bus, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
    
class ArrivalLog(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE)
    arrival_time = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["bus", "stop", "arrival_time"]),
        ]

    def __str__(self):
        return f"{self.bus.bus_number} @ {self.stop.name} -> {self.arrival_time}"

class ETARecord(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    predicted_eta = models.FloatField(help_text="ETA in minutes")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bus.bus_number} ETA: {self.predicted_eta:.2f} min"

class WeatherSnapshot(models.Model):
    timestamp = models.DateTimeField()
    lat = models.FloatField()
    lon = models.FloatField()
    temp_c = models.FloatField(null=True, blank=True)
    precipitation = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    weather_code = models.CharField(max_length=64, blank=True)

class TrafficSnapshot(models.Model):
    timestamp = models.DateTimeField()
    lat = models.FloatField()
    lon = models.FloatField()
    traffic_level = models.FloatField(null=True, blank=True)