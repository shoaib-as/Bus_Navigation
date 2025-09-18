from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from .models import Bus, Stop, LiveLocation, User, ETARecord
from .ml_pipeline import predict_eta as ml_predict_eta, train_model
from .utils import get_address_from_coordinates
from django.conf import settings
import requests

# ----------------------------
# Standard views
# ----------------------------
def home(request):
    return render(request, 'home.html')

def Role(request):
    return render(request, 'Role.html')

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
    locations = LiveLocation.objects.select_related("bus").order_by("-timestamp")[:10]

    location_data = []
    for loc in locations:
        url = f"https://api.tomtom.com/search/2/reverseGeocode/{loc.latitude},{loc.longitude}.json?key={settings.TOMTOM_API_KEY}"
        response = requests.get(url).json()
        address = response.get("addresses", [{}])[0].get("address", {}).get("freeformAddress", "Unknown")
        location_data.append({
            "bus": loc.bus.bus_number,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "address": address,
        })

    return render(request, "bus_map.html", {
        "locations": location_data,
        "buses": location_data,
    })

def user_dashboard(request):
    locations = LiveLocation.objects.all()
    location_data = []

    for loc in locations:
        address = get_address_from_coordinates(loc.latitude, loc.longitude)
        location_data.append({
            "id": loc.id,
            "bus": loc.bus.name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "address": address,
        })

    return render(request, "user_ui/dashboard.html", {"locations": location_data})

def driver_interface(request):
    buses = Bus.objects.all()
    return render(request, 'driver_interface.html', {'buses': buses})


# ----------------------------
# Auth / Registration
# ----------------------------
@csrf_exempt
def auth_view(request):
    context = {"register_active": False}

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "login":
            email = request.POST.get("email")
            password = request.POST.get("password")
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                messages.success(request, "Login successful!")
                return redirect("home")
            context["login_errors"] = "Invalid email or password."

        elif action == "register":
            context["register_active"] = True
            username = request.POST.get("username")
            email = request.POST.get("email")
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")

            if password1 != password2:
                context["register_errors"] = "Passwords do not match."
            elif User.objects.filter(email=email).exists():
                context["register_errors"] = "Email already exists."
            else:
                user = User(username=username, email=email, password=make_password(password1))
                user.save()
                login(request, user)
                messages.success(request, "Registration successful!")
                try:
                    send_mail(
                        subject="Welcome to EventHub!",
                        message=f"Hi {user.username},\n\nThank you for registering at EventHub.",
                        from_email=None,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print("Email sending failed:", e)
                return redirect("home")

    return render(request, "sign-up.html", context)


# ----------------------------
# API: Update bus location
# ----------------------------
@method_decorator(csrf_exempt, name='dispatch')
class UpdateLocation(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        bus_id = data.get("bus_id")
        lat = data.get("latitude")
        lng = data.get("longitude")

        if not all([bus_id, lat, lng]):
            return Response({"status": "error", "message": "Missing data"}, status=400)

        bus = get_object_or_404(Bus, id=bus_id)
        LiveLocation.objects.create(
            bus=bus,
            latitude=lat,
            longitude=lng,
            timestamp=timezone.now()
        )

        return Response({"status": "success"})


@api_view(['GET'])
def get_location(request, bus_id):
    location = LiveLocation.objects.filter(bus_id=bus_id).last()
    if location:
        return Response({
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timestamp": location.timestamp
        })
    return Response({"error": "No location found"}, status=404)


# ----------------------------
# ETA Prediction APIs
# ----------------------------
@api_view(['GET'])
def predict_latest_eta(request, bus_id, stop_lat, stop_lon):
    """Train model automatically and predict ETA for latest bus location."""
    model, df = train_model(stop_lat=float(stop_lat), stop_lon=float(stop_lon))
    if model is None or df.empty:
        return JsonResponse({"error": "Not enough data yet for this route"}, status=400)

    latest_loc = df[df['bus_id'] == int(bus_id)].iloc[-1]
    latest_features = latest_loc.drop(labels=['bus_id', 'timestamp', 'eta']).values.reshape(1, -1)

    predicted = model.predict(latest_features)[0]

    ETARecord.objects.create(
        bus_id=int(bus_id),
        predicted_eta=predicted,
        timestamp=timezone.now()
    )

    return JsonResponse({
        "bus_id": bus_id,
        "predicted_eta_minutes": round(predicted, 2),
        "timestamp": timezone.now()
    })


@api_view(['GET'])
def latest_eta(request, bus_number):
    bus = get_object_or_404(Bus, bus_number=bus_number)
    try:
        latest_record = ETARecord.objects.filter(bus=bus).latest("timestamp")
        return JsonResponse({
            "bus_number": bus.bus_number,
            "predicted_eta_minutes": round(latest_record.predicted_eta, 2),
            "timestamp": latest_record.timestamp
        })
    except ETARecord.DoesNotExist:
        return JsonResponse({"error": "No ETA available yet"}, status=404)
