"""
#===================================================#
#                   set_valve.py                    #
#===================================================#
#  Dieses Skript sendet den Befehl zum oeffnen oder #
#  schliessen eines Ventils an den Mikrocontroller  #
#===================================================#
# Entwickler : Fabian Voelker                       #
#===================================================#
"""

import serial
import sys

uart = serial.Serial('/dev/ttyS0', 9600) # uart initalisieren, baudrate=9600

# Funktionsparameter entgegen nehmen
valve_id_sys = (str(sys.argv[1]))
action_sys = (str(sys.argv[2]))


# Der set_valve Befehl schickt dem Mikrocontroller den Befehl das jeweilige
# Ventil entweder zu oeffnen oder zu schliessen

def set_valve(valve_id, action):
    uart.write(b'\n' + b'valve_id:' + valve_id)
    uart.write(b'\t' + b'STATUS-SET:' + action)
    pass

set_valve(valve_id_sys, action_sys)
