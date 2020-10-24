from webapp.models import *

from pyowm.owm import OWM

from datetime import datetime, timedelta

from timezonefinder import TimezoneFinder

from pytz import timezone, utc

def read_weather():
    args = {}

    # Get Location and API Key - if not exist raise exception
    try:
        user_settings = UserSettings.objects.latest('id')
        owm_api_key = user_settings.owm_api_key
        loc = Location.objects.all()[:1][0]
    except:
        print("Standortdaten oder Koordinaten unzureichend gepflegt")
        return -1

    # Get OWM weather manager
    owm = OWM(owm_api_key)
    weather_manager = owm.weather_manager()

    observer = weather_manager.weather_at_coords(float(loc.latitude), float(loc.longitude))
    weather = observer.weather

    humidity = weather.humidity
    pressure = weather.pressure.get("press")
    temperature = weather.temperature("celsius").get("temp")
    wind = weather.wnd.get("speed")
    if weather.rain.get("1h") is not None:
        rain = weather.rain.get("1h")
    else:
        rain = 0

    # -- Get correct reference_time
    reference_time = weather.reference_time('iso') + "00"
    reference_time_obj = datetime.strptime(reference_time, '%Y-%m-%d %H:%M:%S%z')
    reference_time_obj = reference_time_obj + timedelta(hours=int(loc.utc_offset))

    # # -- Get correct reception_time
    reception_time = observer.reception_time('iso') + "00"
    reception_time_obj = datetime.strptime(reception_time, '%Y-%m-%d %H:%M:%S%z')
    reception_time_obj = reception_time_obj + timedelta(hours=int(loc.utc_offset))

    reference_time_obj = datetime.now()
    reception_time_obj = datetime.now()

    owm_id = weather.weather_code
    weather_status_fk = WeatherStatus.objects.get(owm_id__exact=owm_id)

    try:
        w = WeatherData.objects.get(location_fk__exact=loc, reference_time=reference_time_obj)
        w.humidity = humidity
        w.pressure = pressure
        w.rain = rain
        w.temperature = temperature
        w.wind = wind
        w.weather_status_fk = weather_status_fk
        w.save()
    except:
        w = WeatherData.objects.create(reference_time=reference_time_obj, reception_time=reception_time_obj,
                    location_fk=loc, humidity=humidity, pressure=pressure,
                    rain=rain, temperature=temperature, wind=wind, last_update_time=reference_time_obj,
                    weather_status_fk=weather_status_fk)