"""
#===================================================#
#                   Interface.py                    #
#===================================================#
#  Dieses Skript bildet das Interface zwischen dem  #
#  Django-Framework und der Hardwareansteuerung     #
#  des Raspberry Pi's !                             #
#===================================================#
# Entwickler : Fabian Voelker                       #
#===================================================#
"""


import os
import subprocess
import time
import sys
sys.path.append("..")
from webapp.models import *


# Der set_pump Befehl schickt dem Mikrocontroller den Befehl die jeweilige
# Pumpe entweder ein- oder auszuschalten

def set_pump(pump_id, action):
    if action == "ON" or action == "OFF":
        path = os.path.abspath(os.curdir) + "/sprinkler/controller/set_pump.py"
        subprocess.call(['python2.7', path, pump_id, action])
        print("Pumpe: " + pump_id + " --> " + action)  # Ausgabe in Konsole
    else:
        print("set_pump ERROR")  # Fehlermeldung


# Der set_valve Befehl schickt dem Mikrocontroller den Befehl das jeweilige
# Ventil entweder zu oeffnen oder zu schliessen

def set_valve(valve_id, action):
    if action == "ON" or action == "OFF":
        path = os.path.abspath(os.curdir) + "/sprinkler/controller/set_valve.py"
        subprocess.call(['python2.7', path, valve_id, action])
        print("Ventil: " + valve_id + " --> " + action)  # Ausgabe in Konsole
    else:
        print("set_valve ERROR")  # Fehlermeldung


# Der transfer_plan Befehl schickt dem Mikrocontroller den gesamten aktivierten
# Zeitplan. Dieser wird dann vom Mikrocontroller gespeichert, damit dieser auch
# ohne Weboberflaeche und Raspberry funktionsfaehig den Plan abspielen kann

def transfer_plan(plan):
    # Get necessary objects
    pumps = []
    valves = plan.valve.all()
    for valve in valves:
        if not valve.pump_fk in pumps:
            pumps.append(valve.pump_fk)
    schedules = plan.get_related_schedules()

    # Create string
    header_str = "\nNEWPLAN"

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

    path = os.path.abspath(os.curdir) + "/sprinkler/controller/transfer_plan.py"

    subprocess.call(['python2.7', path, message_str])


# Der delete_plan Befehl schickt dem Mikrocontroller den Befehl den zuvor
# gesendeten und eingespeicherten Plan zu loeschen, um für einen neuen Plan
# bereit zu sein

def delete_plan():
    header_str = "DELETEPLAN"
    message_str = header_str
    print("Message to controller:\n" + message_str)

    path = os.path.abspath(os.curdir) + "/sprinkler/controller/transfer_plan.py"

    subprocess.call(['python2.7', path, message_str])


# Diese Methode soll in Zukunft die Messwerte des Feuchtigkeitssensors entgegennehmen
# und mit in die automatisierte Bewaesserung einbeziehen

def get_humidity(sensor_id):
    pass


# Diese Methode soll den Status des Mikrocontrollers abfragen koennen

def get_status():
    # return status des Microcontrollers
    pass


# Nachdem eine Anfrage an den Mikrocontroller gesendet wurde, wird mit
# dieser Methode gewartet bis eine Antwort im System erscheint

def wait_answer():
    # received_data = uart.read()
    # time.sleep(0.03)
    # data_left = uart.inWaiting()
    # received_data += uart.read(data_left)
    # return received_data
    pass


# Nachdem eine Anfrage an den Mikrocontroller gesendet wurde, wird mit
# dieser Methode ueberprueft, ob alle Daten angekommen sind.

def check_sending(received_data):
    # if received_data== b'OK\r':
        # return True
    # else:
        # return False
    pass