from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('buses/', views.bus_list, name='bus_list'),
    path('stops/', views.stop_list, name='stop_list'),
    path('locations/', views.location_list, name='location_list'),
    path("bus-map/", views.bus_map, name="bus_map"),
]