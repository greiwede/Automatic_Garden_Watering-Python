from django.contrib import admin
from .models import *


# Register your models here.

#admin.site.register(Sprinkler)

#admin.site.register(Pump)

#admin.site.register(Sensor)

admin.site.register(Plan)

#admin.site.register(Schedule)

admin.site.register(Location)

admin.site.register(WeatherData)

admin.site.register(UserSettings)

admin.site.register(WeatherStatus)

admin.site.site_header = "Sprinkler User-Verwaltung"
