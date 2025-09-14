from django.db import models
from django.contrib.auth.models import User

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