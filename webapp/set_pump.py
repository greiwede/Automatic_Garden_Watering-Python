import serial
import time
import sys

uart = serial.Serial('/dev/ttyS0', 9600) # uart initalisieren, baudrate=9600

# Funktionsparameter entgegen nehmen
pump_id_sys = (str(sys.argv[1]))
action_sys = (str(sys.argv[2]))


def set_pump(pump_id, action):
    pass


