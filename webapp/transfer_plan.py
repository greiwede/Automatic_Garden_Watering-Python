import serial
import time
import sys
from .models import *

uart = serial.Serial('/dev/ttyS0', 9600) # uart initalisieren, baudrate=9600

# Funktionsparameter entgegen nehmen
plan_str_sys = sys.argv[1]


def transfer_plan(plan_str):
    uart.write(plan_str_sys)


transfer_plan(plan_str_sys)