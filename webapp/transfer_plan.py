import serial
import time
import sys
from .models import *

uart = serial.Serial('/dev/ttyS0', 9600) # uart initalisieren, baudrate=9600

# Funktionsparameter entgegen nehmen
pumps_sys = sys.argv[1]
valves_sys = sys.argv[2]
schedules_sys = sys.argv[3]


def transfer_plan(pumps, valves, schedules):
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

    uart.write(pumpen_str+"\n"+valves_str+"\n"+ schedules_str)


transfer_plan(pumps_sys, valves_sys, schedules_sys)