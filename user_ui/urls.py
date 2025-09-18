from django.urls import path
from . import views
from .views import get_eta , predict_eta , latest_eta

urlpatterns = [
    # HTML views
    path('', views.home, name='home'),
    path('buses/', views.bus_list, name='bus_list'),
    path('stops/', views.stop_list, name='stop_list'),
    path('locations/', views.location_list, name='location_list'),
    path("bus-map/", views.bus_map, name="bus_map"),
    path('sign-up/', views.auth_view, name='sign-up'),
    path('driver_interface/', views.driver_interface, name='driver_interface'),
    path('Role/', views.Role, name='Role'),
    # API views
    path('api/update-location/', views.UpdateLocation.as_view(), name='update_location'),
    path('api/location/<int:bus_id>/', views.get_location, name='get_location'),

    path("eta/<int:bus_id>/<int:stop_id>/", get_eta, name="bus_eta"),
    path("predict-eta/", predict_eta, name="predict_eta"),
    path("latest-eta/<str:bus_number>/", latest_eta, name="latest_eta"),
]
