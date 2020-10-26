from __future__ import absolute_import, unicode_literals

from datetime import date

from celery import shared_task

from .models import *
from django.db.models import Sum, Max
import time  # test


# test
@shared_task
def add(a, b):
    time.sleep(5)
    return a + b


# test
@shared_task
def print_test():
    file = open("test.txt", "a")
    file.write("test")
    file.close()
    print('test')


@shared_task
def deactivate_valve(valve_id, watering_time):
    time.sleep(watering_time * 1)  # warte Zeit in Sekunden
    valve = Valve.objects.get(pk=valve_id)
    valve.curr_active = False
    valve.save()
    file = open("test.txt", "a")
    file.write(valve.name)
    file.write(str(watering_time))
    file.write("  SChalte das Ventil wieder aus \n")
    file.close()
    # valve.deactivate() # Modelfunktion zum deaktivieren aufrufen
    # stop_valve(valve) # Sende an Microcontroller


@shared_task
def aut_irrigation():
    file = open("test.txt", "a")
    file.write("test \n")
    file.close()
    automatic_plan = get_activ_automatic_plan()
    if automatic_plan is not None:
        file = open("test.txt", "a")
        file.write("auto \n")
        file.close()
        # ist Sprengzeit erlaubt
        if time_allowed():  # Abfrage an Model
            file = open("test.txt", "a")
            file.write("ta \n")
            file.close()
            # mit Bodensensor
            if is_sensor_activ():  # Abfrage an MC
                file = open("test.txt", "a")
                file.write("sensor")
                file.close()
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
                        valve_time = (wateramount * amount_sprinkler) / get_valve_flow_capacity(
                            valve)  # durchschnittliche Bewaesserungszeit fuer jeden Sprinkler des Ventils berechnen
                        set_watering_time_valve(valve, valve_time)
            else:
                file = open("test.txt", "a")
                file.write("valve \n")
                file.close()
                valve_list = get_valve_list(automatic_plan)
                # Schleife - alle Ventile durchgehen
                for valve in valve_list:
                    # Addiere Wetterzaehler zu jeden Ventilzaehler
                    file = open("test.txt", "a")
                    file.write(valve.name)
                    file.write("  \n")
                    file.close()
                    add_weathercounter_to_valve_counter(valve)
                # weather_counter.reset_current_weather_counter(maria_db_connection) #zum testen auskommentiert
                calculate_water_amount_valve()
            # Wassermenge > 0 bei mindestens einem Ventil?
            # valve_max = Valve.objetcs.annotate(Max('watering_time'))  # speicher Ventil mit hochster Zeit
            file = open("test.txt", "a")
            file.write("start Loop Check \n")
            file.close()
            pump_list = get_pump_list(automatic_plan)
            for pump in pump_list:
                valve_list_sort = get_valve_pump_list(automatic_plan, pump).order_by('-watering_time')
                if valve_list_sort.first().watering_time > 0:
                    file = open("test.txt", "a")
                    file.write("Ventil muss angeschaltet werden \n")
                    file.close()
                    # Pumpe bereits eingeschaltet?
                    if pump_deactivated(pump):
                        # Pumpe einschalten
                        start_pump(pump)
                    # Pumpe ausgelastet oder keine Wassermenge > 0?
                    pump_workload_temp = pump_workload(pump)
                    for valve in valve_list_sort:
                        if pump_workload_temp + get_valve_flow_capacity(
                                valve) <= get_pump_flow_capacity(pump) and valve.watering_time > 0:
                            file = open("test.txt", "a")
                            file.write("name und Zeit und Pumpe")
                            file.write(str(valve.watering_time))
                            file.write(valve.name)
                            file.write(pump.name)
                            file.write("\n")
                            file.close()
                            # starte bestimmtes Ventil
                            start_valve(valve.pk, valve.watering_time)
                            deactivate_valve.delay(valve.pk, int(valve.watering_time))
                            # Setze Ventil-Zaehler zurueck
                            pump_workload_temp = pump_workload_temp + get_valve_flow_capacity(valve)
                            valve.watering_time = 0
                            valve.valve_counter = 0
                            valve.curr_active = True
                            valve.save()


def time_allowed():
    return True


def get_sensor_list():
    return Sensor.objects.all()


def get_valve_list(automatic_plan):
    return automatic_plan.valve.filter(
        sprinkler__isnull=False).distinct()  # gebe alle Ventile des automatisierten Plans mit mind. 1 Sprenkler zurueck


def get_valve_pump_list(automatic_plan, pump):
    return get_valve_list(automatic_plan).filter(pump_fk=pump)


def get_pump_list(automatic_plan):
    valves = get_valve_list(automatic_plan)
    return Pump.objects.filter(valve__in=valves).distinct()


def get_valve_sensor_list(sensor):
    return Valve.objects.filter(sensor_fk=sensor)


def set_watering_time_valve(valve, watering_time):
    valve.watering_time = watering_time
    valve.save()


def add_weathercounter_to_valve_counter(valve):
    try:
        valve.valve_counter = valve.valve_counter + WeatherCounter.objects.last().weather_counter
        valve.save()
    except:
        pass


# Platzhalter fuer Pruefung, ob Sensor aktiv
def is_sensor_activ():
    return False


# MUSS  OCH GEAENDERT WERDEN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Wassermenge berechnet fuer mit Sensor
def calculate_water_amount_sensor(sensor):
    wateramount = 0
    rain_amount = 0
    automatic_plan = get_activ_automatic_plan()
    if automatic_plan is not None:
        if automatic_plan.automation_rain:
            if is_rain_activ():
                rain_amount = get_rain_forecast()  # Totzeit des Sensors erstmal nicht beruecksichtigen
            if get_sensor_humidity(sensor) < get_sensor_threshold(automatic_plan):
                # Wettereinfluesse die noch nicht vom Sensor erkannt wurden beruecksichtigen (Totzeit) und Forecast
                wateramount = calc_needed_water_amount(sensor) - rain_amount
                if wateramount < 0:
                    wateramount = 0
            else:
                wateramount = 0
            return 10  # zum testen


def calc_needed_water_amount(sensor):
    sensor_counter = get_sensor_humidity(sensor)
    amount_calc_water = 100 - sensor_counter
    amount_water_new = amount_calc_water  # * Wert pro Prozent
    return amount_water_new


def calculate_water_amount_valve():
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
                if rain_amount > get_water_amount(valve,
                                                  diff_counter_threshold):  # in qm Umrechnen damit vergleich sinnvoll????????????????????????????
                    # Setze Sprengzeit = 0
                    valve_time = 0
                else:
                    water_amount = get_water_amount(valve, diff_counter_threshold) - rain_amount
                    try:
                        valve_time = water_amount / get_valve_flow_capacity(valve)
                    except:
                        valve_time = 0
            else:
                valve_time = 0
            file = open("test.txt", "a")
            file.write("Sprengzeit wird bei Ventil... auf ... gesetzt")
            file.write(str(valve_time))
            file.write(valve.name)
            file.write("\n")
            file.close()
            valve.watering_time = valve_time
            valve.save()


def get_water_amount(valve, diff_counter_threshold):
    amount_sprinkler = Sprinkler.objects.filter(valve_fk=valve).count()
    file = open("test.txt", "a")
    file.write("Anzahl Sprinkler fuer Ventil")
    file.write(str(amount_sprinkler))
    file.write(valve.name)
    file.write("\n")
    file.close()
    return (diff_counter_threshold / 5) * amount_sprinkler


def get_sensor_threshold(automatic_plan):
    return automatic_plan.moisture_threshold


def get_valve_threshold(automatic_plan):
    return automatic_plan.valve_threshold


def get_valve_counter(valve):
    return valve.valve_counter


# Abfrage an MC
def is_rain_activ():
    return True


# wo genau wird das gespeichert?
def get_rain_forecast():
    return 0


# Abfrage an MC
def get_sensor_humidity(sensor):
    return 10


def pump_deactivated(pump):
    return pump.curr_active


def start_pump(pump):  # mit Fabian absprechen
    pass


def start_valve(valve, time):
    pass


def stop_valve(valve):
    pass


def pump_workload(pump):
    valves = Valve.objects.filter(pump_fk=pump, curr_active=True)
    result = 0
    for valve in valves:
        sprinklers = Sprinkler.objects.filter(valve_fk=valve)
        for sprinkler in sprinklers:
            result = result + sprinkler.flow_capacity
    return result


def get_pump_flow_capacity(pump):
    return pump.flow_capacity


def get_valve_flow_capacity(valve):
    result = Sprinkler.objects.filter(valve_fk=valve).aggregate(summe=Sum('flow_capacity'))['summe']
    return result


def get_activ_automatic_plan():
    plans = Plan.objects.filter(is_active_plan=True)
    for plan in plans:
        if plan.automation_rain or plan.automation_sensor or plan.automation_temperature:
            return plan
    return None