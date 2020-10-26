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
    # Get necessary objects
    pumps = []
    valves = plan.valve.all()
    for valve in valves:
        pumps.append(valve.pump_fk)
    schedules = plan.get_related_schedules()

    # Create string
    header_str = "NEWPLAN"

    i = 0
    pumpen_str = "PUMPS:"
    for pump in pumps:
        if i > 0:
            pumpen_str += ","
        pumpen_str += str(pump.contr_id)
        i += 1

    i = 0
    valves_str = "VALVES:"
    for valve in valves:
        if i > 0:
            valves_str += ","
        valves_str += str(valve.contr_id)
        i += 1

    schedules_str = ""
    for schedule in schedules:
        if schedule.is_allow:
            schedule_temp = "ALLOW;"
        else:
            schedule_temp = "DENY;"

        i = 0
        for weekday in schedule.get_weekdays():
            if i > 0:
                schedule_temp += ","
            schedule_temp += str(weekday)
            i += 1

        schedule_temp += ";"
        schedule_temp += str(schedule.time_start) + ";"
        schedule_temp += str(schedule.time_stop)

        schedules_str += schedule_temp + "\n"

    message_str = header_str + "\n" + pumpen_str + "\n" + valves_str + "\n" + schedules_str

    print("Message to controller:\n" + message_str)

    #subprocess.call(['python2.7', '/home/pi/Dev/python-sprinkler/webapp/transfer_plan.py', message_str])


def delete_plan():
    header_str = "DELETEPLAN"
    message_str = header_str
    print("Message to controller:\n" + message_str)

    #subprocess.call(['python2.7', '/home/pi/Dev/python-sprinkler/webapp/transfer_plan.py', message_str])



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