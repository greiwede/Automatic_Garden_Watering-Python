import serial
import time
import sys

uart = serial.Serial('/dev/ttyS0', 9600) # uart initalisieren, baudrate=9600

# Funktionsparameter entgegen nehmen
valve_id_sys = (str(sys.argv[1]))
action_sys = (str(sys.argv[2]))


def set_valve(valve_id, action):
    uart.write(b'\n' + b'valve_id:' + valve_id)
    # print(b'Adressierung von Pumpe: ' + deviceID)
    uart.write(b'\t' + b'STATUS-SET:' + action)
    # print(b'STATUS-SET:' + boolean)
    pass


