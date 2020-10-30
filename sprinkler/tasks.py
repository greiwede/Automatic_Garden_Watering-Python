"""
#===================================================#
#                   tasks.py                        #
#===================================================#
#  Diese Datei beeihaltet die automatisierte        #
#  Bewaesserung, sowie das Einlesen der Wetterdaten #
#===================================================#
# Entwickler : Timon Wilming und Dennis Greiwe      #
#(& Niclas Dagge & Malte Seelhoefer[siehe Methoden])#
#===================================================#
"""

from __future__ import absolute_import, unicode_literals
from celery import shared_task
import sys
sys.path.append("..")
from webapp.models import *
from django.db.models import Sum
import time
from pyowm.owm import OWM
from datetime import datetime, timedelta
from sprinkler.controller.interface import *


@shared_task
def aut_irrigation():
    file = open("auto_irrigation_log.txt", "a")
    file.write("Die Funktion der automatisierten Bewaesserung wird aufgerufen \n")
    file.close()
    automatic_plan = get_activ_automatic_plan()
    # automatischer Plan aktiv?
    if automatic_plan is not None:
        file = open("auto_irrigation_log.txt", "a")
        file.write(" Es ist ein automatisierter Plan aktiv \n")
        file.close()
        # Zeitraum zum Sprengen erlaubt?
        if automatic_plan.is_allow_time():
            file = open("auto_irrigation_log.txt", "a")
            file.write("  Der aktuelle Zeitraum ist erlaubt  \n")
            file.close()
            # mind. 1 Bodensensor aktiv?
            if is_sensor_activ(automatic_plan):
                file = open("auto_irrigation_log.txt", "a")
                file.write("   Es handelt sich um eine automatisierte Bewaesserung mit Sensor \n")
                file.close()
                # alle Sensoren aus Model abrufen
                sensor_list = get_sensor_list()
                # Schleife - Mind. 1 unbearbeiteter Sensor?
                for sensor in sensor_list:
                    # Rufe Methode zur Sprengzeitberechnung inkl Sensor auf
                    wateramount = calculate_water_amount_sensor(sensor)
                    # Alle Ventile, die dem entsprechenden Sensor zugeornet sind in ventil_list speichern
                    valves_list = get_valve_sensor_list(sensor)
                    # Speichere pro Ventil die berechnete Wassermenge
                    for valve in valves_list:
                        amount_sprinkler = Sprinkler.objects.filter(valve_fk=valve).count()
                        valve_time = (wateramount * amount_sprinkler) / get_valve_flow_capacity(
                            valve)  # durchschnittliche Bewaesserungszeit fuer jeden Sprinkler des Ventils berechnen
                        set_watering_time_valve(valve, valve_time)
            else:
                file = open("auto_irrigation_log.txt", "a")
                file.write("   Es handelt sich um eine automatisierte Bewaesserung mit dem Wetterzaehler \n")
                file.close()
                valve_list = get_valve_list(automatic_plan)
                # Schleife - Mind. 1 unbearbeiteter Ventil-Zaehler?
                for valve in valve_list:
                    # Addiere Wetterzaehler zu jeden Ventilzaehler
                    add_weathercounter_to_valve_counter(valve)
                    file = open("auto_irrigation_log.txt", "a")
                    file.write("    Bei dem Ventil mit den Namen ")
                    file.write(valve.name)
                    file.write(" wird der Ventilzaehler auf:")
                    file.write(str(valve.valve_counter))
                    file.write(" geupdatet")
                    file.write("\n")
                    file.close()
                WeatherCounter.objects.last().reset_weather_counter()
                # Rufe Methode zur Sprengzeitberechnung ohne Sensor auf
                calculate_water_amount_valve()
            # Schleife - Alle Pumpen abgearbeitet?
            pump_list = get_pump_list(automatic_plan)
            for pump in pump_list:
                # Liste aller Ventile einer Pumpe nach (watering_time absteigend sortiert)
                valve_list_sort = get_valve_pump_list(automatic_plan, pump).order_by('-watering_time')
                # Sprengzeit > 0 bei mind. 1 Ventil?
                if valve_list_sort.first().watering_time > 0:
                    file = open("auto_irrigation_log.txt", "a")
                    file.write("      Es existiert ein Ventil mit einer Sprengzeit groesser als 0\n")
                    file.close()
                    # Schleife - Ventile der jeweiligen Pumpe
                    for valve in valve_list_sort:
                        # Pumpe ausgelastet oder keine Wassermenge > 0?
                        if get_pump_workload(pump) + get_valve_flow_capacity(
                                valve) <= get_pump_flow_capacity(pump) and valve.watering_time > 0:
                            file = open("auto_irrigation_log.txt", "a")
                            file.write("       Das Ventil ")
                            file.write(valve.name)
                            file.write(" wird mit einer Dauer von ")
                            file.write(str(valve.watering_time))
                            file.write(" Minuten angeschaltet")
                            file.write("\n")
                            file.close()
                            if time_allowed_timedelta(automatic_plan, valve.watering_time):
                                if valve.curr_active is False:
                                    valve.activate()
                                    # rufe deaktiviere-Methode auf( ueber Celery)
                                    # diese wartet solange, bis das Ventil deaktiviert werden muss
                                    deactivate_valve.delay(valve.id, int(valve.watering_time))
                                    # reset valve.watering_time and valve.valve_counter
                                    valve.watering_time = 0
                                    valve.valve_counter = 0
                                    valve.save()


@shared_task
def deactivate_valve(valve_id, watering_time):
    time.sleep(watering_time * 60)  # warte Zeit in Sekunden
    valve = Valve.objects.get(pk=valve_id)
    file = open("auto_irrigation_log.txt", "a")
    file.write("        Das Ventil ")
    file.write(valve.name)
    file.write(" wird nach einer Dauer von ")
    file.write(str(watering_time))
    file.write(" Minuten ausgeschaltet")
    file.write("\n")
    valve.deactivate() # Modelfunktion zum deaktivieren aufrufen


def calculate_water_amount_valve():
    """
    Entwickler: Niclas Dagge & Dennis Greiwe

    Berechnung der benoetigten Wassermenge, wenn kein Bodenfeuchtigkeitssensor aktiv ist
    """
    valve_time = 0
    rain_amount = 0
    automatic_plan = get_activ_automatic_plan()
    if automatic_plan is not None:
        if automatic_plan.automation_rain:
            rain_amount = get_rain_forecast()
        # alle Ventile abrufen
        valve_list = get_valve_list(automatic_plan)
        # Schleife fuer alle Ventile
        for valve in valve_list:
            current_valve_counter = get_valve_counter(valve)
            # Ventil-Zaehler > Schwellwert
            if current_valve_counter > get_valve_threshold(automatic_plan):
                diff_counter_threshold = current_valve_counter - get_valve_threshold(automatic_plan)
                # Niederschlagsmenge der vorgegebenen Zeitspanne groesser als benoetigte Wassermenge?
                # rain Forecast flaeche umrechnen
                if rain_amount > get_water_amount(valve,
                                                  diff_counter_threshold):
                    # Setze Sprengzeit = 0
                    valve_time = 0
                else:
                    water_amount = (get_water_amount(valve, diff_counter_threshold) - rain_amount) * get_valve_area(valve)
                    # Try, da falls kein Sprinkler zum Ventil zugeordnet ist ein Fehler in der Berechnung auftritt
                    try:
                        valve_time = water_amount / get_valve_flow_capacity(valve)
                    except:
                        valve_time = 0
            else:
                valve_time = 0
            file = open("auto_irrigation_log.txt", "a")
            file.write("     Sprengzeit wird bei Ventil ")
            file.write(valve.name)
            file.write(" auf den Wert ")
            file.write(str(valve_time))
            file.write(" gesetzt ")
            file.write("\n")
            file.close()
            valve.watering_time = valve_time
            valve.save()


def get_water_amount(valve, diff_counter_threshold):
    """
    Entwickler: Niclas Dagge

    Ermittelt die benoetigte Wassermenge des uebergebenen Ventils
    """
    amount_sprinkler = Sprinkler.objects.filter(valve_fk=valve).count()
    return (diff_counter_threshold / 5) * amount_sprinkler


def get_valve_area(valve):
    """
    Entwickler: Niclas Dagge

    Ermittelt aus Durchflussmenge einen ungefaehren Wert fuer die Quadratmeteranzahl eines Ventils
    """
    flow_capacity_hours = get_valve_flow_capacity(valve) * 60
    if 200 <= flow_capacity_hours < 300:
        return 10
    elif 300 <= flow_capacity_hours < 400:
        return 15
    elif 400 <=flow_capacity_hours < 500:
        return 20
    elif 500 <= flow_capacity_hours < 600:
        return 25
    elif 600 <= flow_capacity_hours < 700:
        return 30
    elif 700 <= flow_capacity_hours < 900:
        return 40
    elif 900 <= flow_capacity_hours < 1100:
        return 50
    elif 1100 <= flow_capacity_hours < 1500:
        return 70
    elif 1500 <= flow_capacity_hours < 2000:
        return 100
    elif 2000 <= flow_capacity_hours:
        return 150
    else:
        return 1


def calculate_water_amount_sensor(sensor):
    """
    Entwickler: Niclas Dagge & Dennis Greiwe

    Berechnung der benoetigten Wassermenge, wenn mindestens ein Bodenfeuchtigkeitssensor aktiv ist
    """
    rain_amount = 0
    automatic_plan = get_activ_automatic_plan()
    if automatic_plan is not None:
        if automatic_plan.automation_rain:
            if automatic_plan.automation_rain:
                rain_amount = get_rain_forecast()  # Totzeit des Sensors erstmal nicht beruecksichtigen
            if get_sensor_humidity(sensor) < get_sensor_threshold(automatic_plan):
                wateramount = calc_needed_water_amount(sensor) - rain_amount
                if wateramount < 0:
                    wateramount = 0
            else:
                wateramount = 0
            return wateramount


def calc_needed_water_amount(sensor):
    """
    Entwickler: Niclas Dagge

    Ermittelt die benoetigte Wassermenge fuer ein Ventil auf Grundlage der Sensordaten
    """
    sensor_counter = get_sensor_humidity(sensor)
    amount_calc_water = 100 - sensor_counter
    amount_water_new = amount_calc_water * 0.2
    return amount_water_new


def time_allowed_timedelta(plan, time):
    """Ermittelt aus der Datenbank, ob wahrend des Ablaufs der uebergeben Zeit die Sperrezeit zum Sprengen erreicht wird"""
    next_denied_time = plan.get_next_denied_start_date_time()
    if(next_denied_time is not None):
        time_valve_deactivate = datetime.datetime.now() + timedelta(minutes=int(time))
        if (next_denied_time > time_valve_deactivate):
            return True
        else:
            return False
    else: # keine Verbotszeiten -> immer True
        return True


def get_sensor_list():
    """Erstellt eine Liste aller in der Datenbank gespeicherten Sensoren"""
    return Sensor.objects.all()


def get_valve_list(automatic_plan):
    """Erstellt eine Liste aller in der Datenbank gespeicherten Ventile, welche im automatischen Plan vorhanden sind"""
    return automatic_plan.valve.filter(sprinkler__isnull=False).distinct()


def get_valve_pump_list(automatic_plan, pump):
    """Erstellt eine Liste aller in der Datenbank gespeicherten Ventile , die an der uebergebenen Pumpe angeschlossen sind"""
    return get_valve_list(automatic_plan).filter(pump_fk=pump)


def get_pump_list(automatic_plan):
    """Erstellt eine Liste aller in der Datenbank gespeicherten Pumpen, welche im automatischen Plan vorhanden sind"""
    valves = get_valve_list(automatic_plan)
    return Pump.objects.filter(valve__in=valves).distinct()


def get_valve_sensor_list(sensor):
    """Erstellt eine Liste aller Ventile in der Datenbank, die mit dem uebergebenen Sensor bearbeitet werden"""
    return Valve.objects.filter(sensor_fk=sensor)


def set_watering_time_valve(valve, watering_time):
    """Setzt den uebergebenen Wert fuer die Bewaesserungszeit in der Datenbank entsprechend der uebergebenen Bewaesserungszeit"""
    valve.watering_time = watering_time
    valve.save()


def add_weathercounter_to_valve_counter(valve):
    """Erhoeht den Wert fuer den Ventilzaehler in der Datenbank um den Wetterzaehler"""
    try:
        valve.valve_counter = valve.valve_counter + WeatherCounter.objects.last().weather_counter
        valve.save()
    except:
        WeatherCounter.objects.create(weather_counter=0)


def is_sensor_activ(plan):
    """Ermittelt aus der Datenbank, ob mindestens ein Bodenfeuchtigkeitssensor aktiv ist"""
    return plan.automation_sensor


def get_sensor_threshold(automatic_plan):
    """Liest Grenzwert des Bodenfeuchtigkeitssensors, um mit dem Sprengen zu beginnen, aus der Datenbank aus"""
    return automatic_plan.moisture_threshold


def get_valve_threshold(automatic_plan):
    """Liest Grenzwert des Ventils, um mit dem Sprengen zu beginnen,  aus der Datenbank aus"""
    return automatic_plan.valve_threshold


def get_valve_counter(valve):
    """Liest Wetterzaehler des uebergebenen Ventils aus der Datenbank aus"""
    return valve.valve_counter


def get_rain_forecast():
    """Ermittelt aus der Datenbank den Regen ueber einen bestimmten Zeitraum in der Zukunft"""
    return 0


def get_sensor_humidity(sensor):
    """Ermittelt Wert des Bodenfeuchtigkeitssensors durch Kommunikation mit dem Mikrocontroller"""
    # return get_humidity(sensor.id) # Abfrage an MC
    return 10 # Testwert, da MC-Funktion noch nicht vollstaendig


def get_pump_workload(pump):
    """Ermittelt aus der Datenbank momentane Auslastung der uebergebenen Pumpe"""
    return pump.current_workload


def get_pump_flow_capacity(pump):
    """Ermittelt aus der Datenbank maximale Wasserauslastung der uebergebenen Pumpe"""
    return pump.flow_capacity


def get_valve_flow_capacity(valve):
    """Ermittelt aus Datenbank Durchflussmenge des uebergebenen Ventils"""
    result = Sprinkler.objects.filter(valve_fk=valve).aggregate(summe=Sum('flow_capacity'))['summe']
    return result


def get_activ_automatic_plan():
    """Ermittelt aus der Datenbank, ob ein automatiserter Plan aktiv ist und wenn ja welcher"""
    plans = Plan.objects.filter(is_active_plan=True)
    for plan in plans:
        if plan.automation_rain or plan.automation_sensor or plan.automation_temperature:
            return plan
    return None


@shared_task
def read_weather():
    """Entwickler: Malte Seelhoefer"""
    args = {}

    # Get Location and API Key - if not exist raise exception
    try:
        user_settings = UserSettings.objects.last()
        owm_api_key = user_settings.owm_api_key
        loc = Location.objects.last()
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

    # Get correct reference_time
    if(platform.system()=='Linux'):
        reference_time = weather.reference_time('iso')
    elif(platform.system()=='Windows'):
        reference_time = weather.reference_time('iso') + "00" # Needed under Windows OS
    reference_time_obj = datetime.datetime.strptime(reference_time, '%Y-%m-%d %H:%M:%S%z')
    reference_time_obj = reference_time_obj + timedelta(hours=int(loc.utc_offset))

    # Get correct reception_time
    if(platform.system()=='Linux'):
        reception_time = observer.reception_time('iso')
    elif(platform.system()=='Windows'):
        reception_time = observer.reception_time('iso') + "00" # Needed under Windows OS
    reception_time_obj = datetime.datetime.strptime(reception_time, '%Y-%m-%d %H:%M:%S%z')
    reception_time_obj = reception_time_obj + timedelta(hours=int(loc.utc_offset))

    reference_time_obj = datetime.datetime.now()
    reception_time_obj = datetime.datetime.now()

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

    # Update weather counter
    try:
        wc = WeatherCounter.objects.last()
        wc.modify_weather_counter()
        wc.save()
    except:
        wc = WeatherCounter.objects.create(weather_counter=0)
        wc.modify_weather_counter()
        wc.save()


@shared_task
def manual_irrigation():
    """First gets an active plan if there is one. Then if it is watering time it opens the associated valves."""
    try:
        active_plan = Plan.objects.get(is_active_plan=True)
    except:
        print("No active plan found.")
    
    if active_plan.is_allow_time():
        valves = active_plan.valve.all()
        for valve in valves:
            valve.activate()
    else:
        print("No watering time currently.")