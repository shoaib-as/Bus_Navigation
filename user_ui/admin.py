from django.contrib import admin
from .models import Bus, Stop, LiveLocation, DriverProfile

admin.site.register(Bus)
admin.site.register(Stop)
admin.site.register(LiveLocation)
admin.site.register(DriverProfile)