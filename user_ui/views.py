from django.shortcuts import render
from .models import Bus, Stop, LiveLocation
from django.core.serializers import serialize
import json
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from ml_model.baseline_eta import estimate_eta


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

@csrf_exempt
def auth_view(request):
    context = {"register_active": False}

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "login":
            email = request.POST.get("email")
            password = request.POST.get("password")
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, "Login successful!")
                return redirect("home")
            else:
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
                        message=f"Hi {user.username},\n\nThank you for registering at EventHub. Start exploring exciting events now!",
                        from_email=None,  # Uses DEFAULT_FROM_EMAIL
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print("Email sending failed:", e)
                return redirect("home")

    return render(request, "sign-up.html", context)


@api_view(['GET'])
def get_location(request, bus_id):
    location = LiveLocation.objects.filter(bus_id=bus_id).last()
    return Response({
        "latitude": location.latitude,
        "longitude": location.longitude,
        "timestamp": location.timestamp
    })


def driver_interface(request):
    buses = Bus.objects.all()
    return render(request, 'driver_interface.html', {'buses': buses})


from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny

@method_decorator(csrf_exempt, name='dispatch')
class UpdateLocation(APIView):
    authentication_classes = []  # disables SessionAuthentication (no CSRF enforcement)
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        bus_id = data.get("bus_id")
        lat = data.get("latitude")
        lng = data.get("longitude")

        if not all([bus_id, lat, lng]):
            return Response({"status": "error", "message": "Missing data"}, status=400)

        try:
            bus = Bus.objects.get(id=bus_id)
        except Bus.DoesNotExist:
            return Response({"status": "error", "message": "Bus not found"}, status=404)

        LiveLocation.objects.create(
            bus=bus,
            latitude=lat,
            longitude=lng,
            timestamp=timezone.now()
        )
        return Response({"status": "success"})


def get_eta(request, bus_id, stop_id):
    eta = estimate_eta(bus_id, stop_id)
    return JsonResponse({"bus_id": bus_id, "stop_id": stop_id, "eta_minutes": eta})

from .ml_pipeline import train_model

def predict_eta(request):
    model, df = train_model()
    if model is None:
        return JsonResponse({"error": "Not enough data yet"})

    latest = df.iloc[-1][["latitude", "longitude", "speed", "hour", "minute"]].values.reshape(1, -1)
    prediction = model.predict(latest)[0]

    return JsonResponse({"predicted_eta_minutes": round(prediction, 2)})

from .ml_pipeline import train_model
from .models import ETARecord

def predict_eta(request):
    model, df = train_model()
    if model is None:
        return JsonResponse({"error": "Not enough data yet"})

    latest = df.iloc[-1][["latitude", "longitude", "speed", "hour", "minute"]].values.reshape(1, -1)
    prediction = model.predict(latest)[0]

    bus_id = int(df.iloc[-1]["bus_id"])
    ETARecord.objects.create(bus_id=bus_id, predicted_eta=prediction)

    return JsonResponse({"predicted_eta_minutes": round(prediction, 2)})
