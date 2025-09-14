from django.shortcuts import render
from .models import Bus, Stop, LiveLocation
from django.core.serializers import serialize
import json

def home(request):
    return render(request, 'home.html')

def bus_list(request):
    buses = Bus.objects.all()
    return render(request, 'bus_list.html', {'buses': buses})

def stop_list(request):
    stops = Stop.objects.all()
    return render(request, 'stop_list.html', {'stops': stops})

def location_list(request):
    locations = LiveLocation.objects.all().select_related('bus')
    return render(request, 'location_list.html', {'locations': locations})

def bus_map(request):
    buses = Bus.objects.all()
    buses_json = json.dumps([
        {"bus_number": bus.bus_number, "latitude": bus.latitude, "longitude": bus.longitude} 
        for bus in buses
    ])
    return render(request, 'bus_map.html', {'buses': buses_json})