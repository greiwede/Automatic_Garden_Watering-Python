from __future__ import absolute_import, unicode_literals

from datetime import date

from celery import shared_task

from .models import *
from .interface import *
from django.db.models import Sum
import time

@shared_task
def deactivate_valve(valve_id, watering_time):
    time.sleep(watering_time * 60)  # warte Zeit in Sekunden
    valve = Valve.objects.get(pk=valve_id)
    file = open("test.txt", "a")
    file.write("        Das Ventil ")
    file.write(valve.name)
    file.write(" wird nach einer Dauer von ")
    file.write(str(watering_time * 60))
    file.write(" Minuten ausgeschaltet")
    file.write("\n")
    valve.deactivate() # Modelfunktion zum deaktivieren aufrufen


@shared_task
def aut_irrigation():
    file = open("test.txt", "a")
    file.write("Die Funktion der automatisierten Bewaesserung wird aufgerufen \n")
    file.close()
    automatic_plan = get_activ_automatic_plan()
    if automatic_plan is not None:
        file = open("test.txt", "a")
        file.write(" Es ist ein automatisierter Plan aktiv \n")
        file.close()
        # ist Sprengzeit erlaubt
        if time_allowed():  # Abfrage an Model
            file = open("test.txt", "a")
            file.write("  Der aktuelle Zeitraum ist erlaubt  \n")
            file.close()
            # mit Bodensensor
            if is_sensor_activ(automatic_plan):
                file = open("test.txt", "a")
                file.write("   Es handelt sich um eine automatisierte Bewaesserung mit Sensor \n")
                file.close()
                # alle Sensoren aus Model abrufen
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
                file.write("   Es handelt sich um eine automatisierte Bewaesserung mit dem Wetterzaehler \n")
                file.close()
                valve_list = get_valve_list(automatic_plan)
                # Schleife - alle Ventile durchgehen
                for valve in valve_list:
                    # Addiere Wetterzaehler zu jeden Ventilzaehler
                    add_weathercounter_to_valve_counter(valve)
                    file = open("test.txt", "a")
                    file.write("    Bei dem Ventil mit den Namen ")
                    file.write(valve.name)
                    file.write(" wird der Ventilzaehler auf:")
                    file.write(str(valve.valve_counter))
                    file.write(" geupdatet")
                    file.write("\n")
                    file.close()
                WeatherCounter.objects.last().reset_weather_counter()
                calculate_water_amount_valve()
            # Loop Pumpe
            pump_list = get_pump_list(automatic_plan)
            for pump in pump_list:
                # Liste aller Ventile einer Pumpe nach (watering_time absteigend sortiert)
                valve_list_sort = get_valve_pump_list(automatic_plan, pump).order_by('-watering_time')
                # Wassermenge > 0 bei mindestens einem Ventil?
                if valve_list_sort.first().watering_time > 0:
                    file = open("test.txt", "a")
                    file.write("      Es existiert ein Ventil mit einer Sprengzeit groesser als \n")
                    file.close()
                    # Loop Ventile der jeweiligen Pumpe
                    for valve in valve_list_sort:
                        # Pumpe ausgelastet oder keine Wassermenge > 0?
                        if get_pump_workload(pump) + get_valve_flow_capacity(
                                valve) <= get_pump_flow_capacity(pump) and valve.watering_time > 0:
                            file = open("test.txt", "a")
                            file.write("       Das Ventil ")
                            file.write(valve.name)
                            file.write(" wird mit einer Dauer von ")
                            file.write(str(valve.watering_time*60))
                            file.write(" Minuten angeschaltet")
                            file.write("\n")
                            file.close()
                            # starte bestimmtes Ventil
                            ##########
                            # Sprengzeit während der gesamten Sprengdauer erlaubt? ergänzen
                            ##########
                            valve.activate()
                            # rufe deaktiviere-Methode auf( ueber Celery)
                            # diese wartet solange, bis das Ventil deaktiviert werden muss
                            deactivate_valve.delay(valve.id, int(valve.watering_time))
                            # reset valve.watering_time and valve.valve_counter
                            valve.watering_time = 0
                            valve.valve_counter = 0
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
        WeatherCounter.objects.create(weather_counter=0)


def is_sensor_activ(plan):
    return plan.automation_sensor


# MUSS  OCH GEAENDERT WERDEN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Wassermenge berechnet fuer mit Sensor
def calculate_water_amount_sensor(sensor):
    wateramount = 0
    rain_amount = 0
    automatic_plan = get_activ_automatic_plan()
    if automatic_plan is not None:
        if automatic_plan.automation_rain:
            if automatic_plan.automation_rain:
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
    amount_water_new = amount_calc_water * 0.2
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
                # rain Forecast flaeche umrechnen
                if rain_amount > get_water_amount(valve,
                                                  diff_counter_threshold):
                    # Setze Sprengzeit = 0
                    valve_time = 0
                else:
                    water_amount = get_water_amount(valve, diff_counter_threshold) - rain_amount
                    # Try, da falls kein Sprinkler zum Ventil zugeordnet ist ein Fehler in der Berechnung auftritt
                    try:
                        valve_time = water_amount / get_valve_flow_capacity(valve)
                    except:
                        valve_time = 0
            else:
                valve_time = 0
            file = open("test.txt", "a")
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


# wo genau wird das gespeichert?
def get_rain_forecast():
    return 0


def get_sensor_humidity(sensor):
    return 10


def is_pump_deactivated(pump):
    return pump.curr_active


def get_pump_workload(pump):
    return pump.current_workload


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