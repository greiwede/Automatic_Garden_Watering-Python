import os
import subprocess
import time
from .models import *


def set_pump(pump_id, action):
    subprocess.call(['python2.7','/meinPfad/sprinkler-sprinkler/webapp/set_pump.py', pump_id, action])
    print("Pumpe: " + pump_id + " --> " + action) # Ausgabe in Konsole


def set_valve(valve_id, action):
    subprocess.call(['python2.7','/meinPfad/sprinkler-sprinkler/webapp/set_valve.py', valve_id, action])
    print("Ventil: " + valve_id + " --> " + action)  # Ausgabe in Konsole


def transfer_plan():
    pass


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