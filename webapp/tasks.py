from __future__ import absolute_import, unicode_literals

from datetime import date

from celery import shared_task

from .models import *
import time # test


#test
@shared_task
def add(a,b):
    time.sleep(5)
    return a+b

#test
@shared_task
def print_test():
    file = open("test.txt","a")
    file.write("test")
    file.close()
    print('test')

@shared_task
def aut_irrigation():
    automatic_plan = WeatherCounter.get_activ_automatic_plan()
    if automatic_plan is not None:
        # ist Sprengzeit erlaubt
        if time_allowed: # Abfrage an Model
            # mit Bodensensor
            if is_sensor_activ: # Abfrage an MC
                # alle Sensor-IDs aus DB abrufen
                sensor_list = get_sensor_list()
                # Schleife - alle Sensoren durchgehen
                for sensor in sensor_list:
                    # Methode zur Wassermengenberechnung für den jeweiligen Sensor aufrufen
                    wateramount = calculate_water_amount_sensor(sensor)
                    # Alle Ventile, die dem entsprechenden Sensor zugeornet sind in ventil_list speichern
                    valves_list = get_valve_sensor_list(sensor)
                    # jeden Ventil die Wassermenge zuweisen
                    for valve in valves_list:
                        amount_sprinkler = Sprinkler.objects.filter(valve_fk=valve).count()
                        valve_time = (wateramount*amount_sprinkler) / get_valve_water_per_minute(valve) #durchschnittliche Bewaesserungszeit fuer jeden Sprinkler des Ventils berechnen
                        set_watering_time_valve(valve, valve_time)
            else:
                # alle Ventil-IDs aus DB abrufen
                valve_list = get_valve_list()
                # Schleife - alle Ventile durchgehen
                current_weather_counter = 1
                for valve in valve_list:
                    # Addiere Wetterzaehler zu jeden Ventilzaehler
                    add_weathercounter_to_valve_counter(valve, current_weather_counter)
                #weather_counter.reset_current_weather_counter(maria_db_connection)
                calculate_water_amount_valve()
            # Wassermenge > 0 bei mindestens einem Ventil?
            valve_list = get_valve_list()
            valve_wateramount_list = valve_list.wateramount
            if max(valve_wateramount_list) > 0:
                # berechne zu sprengende Zeit
                i = 1
                valve_water_per_minute = get_valves_water_per_minute()
                for valve in valve_list:
                    valve_time[i] = valve_wateramount_list[i] / valve_water_per_minute[i]
                    i += 1
                # Pumpe bereits eingeschaltet?
                if pump_deactivated():
                    # Pumpe einschalten
                    start_pump()
                # Pumpe ausgelastet oder keine Wassermenge > 0?
                pump_workload_temp = pump_workload()
                while pump_workload_temp + valve_wateramount_list[max(valve_time)] <= get_pump_flow_capacity() and valve_wateramount_list[max(valve_time)] > 0:
                    current_valve_id = valve_time.index(max(valve_time))
                    # starte bestimmtes Ventil
                    start_valve(current_valve_id, valve_time[current_valve_id])
                    # Setze Ventil-Zaehler zurueck
                    pump_workload_temp = pump_workload_temp + valve_wateramount_list[current_valve_id]
                    valve_wateramount_list[current_valve_id] = 0


def time_allowed():
    date_today = date.today()
    # 0 - Montag bis 6-Sonntag
    day = date_today.weekday()
    # Sperrzeiten aus der Datenbank abrufen und pruefen, ob Sprengen aktuell erlaubt
    return True


def get_sensor_list():
    return Sensor.objects.all()


def get_valve_list():
    return Valve.objects.all()


def get_valve_sensor_list(sensor):
    return Valve.objects.filter(sensor_fk=sensor)


def set_watering_time_valve(valve, watering_time):
    valve.watering_time = watering_time
    valve.save()


def add_weathercounter_to_valve_counter(valve, weather_counter):
    valve.valve_counter = valve.valve_counter + weather_counter
    valve.save()


# Platzhalter fuer Pruefung, ob Sensor aktiv
def is_sensor_activ():
    return True

# MUSS  OCH GEAENDERT WERDEN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Wassermenge berechnet fuer mit Sensor
def calculate_water_amount_sensor(sensor):
    wateramount = 0
    rain_amount = 0
    automatic_plan = WeatherCounter.get_activ_automatic_plan()
    if automatic_plan is not None:
        if automatic_plan.automation_rain:
            if is_rain_activ():
                rain_amount = get_rain_forecast() # Totzeit des Sensors erstmal nicht beruecksichtigen
            if get_sensor_humidity(sensor) < get_sensor_threshold(sensor):
                # Wettereinfluesse die noch nicht vom Sensor erkannt wurden beruecksichtigen (Totzeit) und Forecast
                wateramount = calc_needed_water_amount(sensor) - rain_amount
                if wateramount < 0:
                    wateramount = 0
            else:
                wateramount = 0
            return 10  # zum testen


def calc_needed_water_amount (sensor):
    sensor_counter = get_sensor_humidity(sensor)
    amount_calc_water = 100 - sensor_counter
    amount_water_new = amount_calc_water # * Wert pro Prozent
    return amount_water_new


def calculate_water_amount_valve():
    valve_time = 0
    rain_amount = 0
    automatic_plan = WeatherCounter.get_activ_automatic_plan()
    if automatic_plan is not None:
        if automatic_plan.automation_rain:
            rain_amount = get_rain_forecast()
        # alle Ventile abrufen
        valve_list = get_valve_list()
        # Schleife fuer alle Ventile
        for valve in valve_list:
            current_valve_counter = get_valve_counter(valve)
            #Ventil-Zaehler > Schwellwert
            if current_valve_counter > get_valve_threshold(valve):
                diff_counter_threshold = current_valve_counter - get_valve_threshold(valve)
                #Niederschlagsmenge der vorgegebenen Zeitspanne groesser als benoetigte Wassermenge?
                if rain_amount > get_water_amount(valve, diff_counter_threshold):  # in qm Umrechnen damit vergleich sinnvoll????????????????????????????
                    #Setze Sprengzeit = 0
                    valve_time = 0
                else:
                    water_amount = get_water_amount(valve, diff_counter_threshold) - rain_amount
                    valve_time = water_amount / get_valve_water_per_minute(valve)
            else:
                valve_time= 0
            valve.watering_time = valve_time
            valve.save()


def get_water_amount(self, valve, diff_counter_threshold):
    amount_sprinkler = Sprinkler.objects.filter(valve_fk=valve).count()
    return (diff_counter_threshold / 5) * amount_sprinkler


def get_sensor_threshold(sensor):
    return sensor.moisture_threshold


def get_valve_threshold(valve):
    return valve.valve_threshold


def get_valve_counter(valve):
    return valve.valve_counter


# Abfrage an MC
def is_rain_activ():
    return True


#wo genau wird das gespeichert?
def get_rain_forecast():
    return 15

#Abfrage an MC
def get_sensor_humidity(sensor):
    return 10

#wahrscheinlich nicht mehr benoetigt
def get_rain_last_hour():
    return 0

# wahrscheinlich nicht mehr benoetigt
def get_sprinkler_last_hour():
    return 10

def calc_needed_water_amount():
    return 20


def pump_deactivated():
    return Pump.getObjects.First().active  # evtl ID ergaenzen statt first


    # Code unvollstaendig
def start_pump(): # mit Fabian absprechen
    pass


def pump_workload():
    return Pump.getObjects.First().workload # evtl ID ergaenzen statt first


def get_pump_flow_capacity():
    return Pump.getObjects.First().flow_capacity  # evtl ID ergaenzen statt first


def get_valve_water_per_minute(valve):
    result = Sprinkler.objects.get(valve_fk = valve).aggregate(Sum('Durchflussmenge'))
    return results

