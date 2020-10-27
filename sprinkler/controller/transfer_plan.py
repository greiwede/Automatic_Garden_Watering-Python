"""
#===================================================#
#                 transfer_plan.py                  #
#===================================================#
#      Dieses Skript sendet den Plan an den         #
#     Mikrocontroller, der diesen abspeichert       #
#===================================================#
# Entwickler : Fabian Voelker                       #
#===================================================#
"""

import serial
import sys

uart = serial.Serial('/dev/ttyS0', 9600) # uart initalisieren, baudrate=9600

# Funktionsparameter entgegen nehmen
plan_str_sys = sys.argv[1]


# Der transfer_plan Befehl schickt dem Mikrocontroller den gesamten aktivierten
# Zeitplan. Dieser wird dann vom Mikrocontroller gespeichert, damit dieser auch
# ohne Weboberflaeche und Raspberry funktionsfaehig den Plan abspielen kann

def transfer_plan(plan_str):
    uart.write(plan_str_sys)


transfer_plan(plan_str_sys)