import os
import subprocess
import time
from .models import *

# Pfad Problem!

def set_pump(pump_id, action):
    if action == "ON" or action == "OFF":
        subprocess.call(['python2.7', '/home/pi/Dev/python-sprinkler/webapp/set_pump.py', pump_id, action])
        print("Pumpe: " + pump_id + " --> " + action)  # Ausgabe in Konsole
    else:
        print("set_pump ERROR")  # Fehlermeldung


def set_valve(valve_id, action):
    if action == "ON" or action == "OFF":
        subprocess.call(['python2.7', '/home/pi/Dev/python-sprinkler/webapp/set_valve.py', valve_id, action])
        print("Ventil: " + valve_id + " --> " + action)  # Ausgabe in Konsole
    else:
        print("set_valve ERROR")  # Fehlermeldung


def transfer_plan(plan):
    pumps = []
    valves = plan.valve.all()
    for valve in valves:
        pumps.append(valve.pump_fk)
    schedules = plan.get_related_schedules()

    pumpen_str = "Pumpen: "
    for pump in pumps:
        pumpen_str += pump.contr_id + ","

    valves_str = "Ventile: "
    for valve in valves:
        valves_str += valve.contr_id + ","

    schedules_str = ""
    for schedule in schedules:
        if schedule.is_allow():
            schedule_temp = "ALLOW;"
        else:
            schedule_temp = "DENY;"

        for weekday in schedule.get_weekdays():
            schedule_temp += weekday + ","

        schedule_temp += ";"
        schedule_temp += schedule.start_time + ";"
        schedule_temp += schedule.end_time

        schedules_str += schedule_temp + "\n"

    plan_str = pumpen_str + "\n" + valves_str + "\n" + schedules_str

    subprocess.call(['python2.7', '/home/pi/Dev/python-sprinkler/webapp/transfer_plan.py', plan_str])


def get_humidity(sensor_id):
    pass


def get_status():
    # return status des Microcontrollers
    pass


def wait_answer():
    # received_data = uart.read()
    # time.sleep(0.03)
    # data_left = uart.inWaiting()
    # received_data += uart.read(data_left)
    # return received_data
    pass


def check_sending(received_data):
    # if received_data== b'OK\r':
        # return True
    # else:
        # return False
    pass