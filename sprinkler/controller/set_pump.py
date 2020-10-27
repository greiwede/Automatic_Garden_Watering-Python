"""
#===================================================#
#                   set_pump.py                     #
#===================================================#
#  Dieses Skript sendet den Befehl zum an- oder     #
#  ausschalten der Pumpe an den Mikrocontroller     #
#===================================================#
# Entwickler : Fabian Völker                        #
#===================================================#
"""

import serial
import sys

uart = serial.Serial('/dev/ttyS0', 9600) # uart initalisieren, baudrate=9600

# Funktionsparameter entgegen nehmen
pump_id_sys = (str(sys.argv[1]))
action_sys = (str(sys.argv[2]))


# Der set_pump Befehl schickt dem Mikrocontroller den Befehl die jeweilige
# Pumpe entweder ein- oder auszuschalten

def set_pump(pump_id, action):
    uart.write(b'\n' + b'pump_id:' + pump_id)
    uart.write(b'\t' + b'STATUS-SET:' + action)
    pass

set_pump(pump_id_sys, action_sys)

