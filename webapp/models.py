"""
#===================================================#
#                   views.py                        #
#===================================================#
#  This file contains all the database models and relations      #
#===================================================#
# Developers: Malte Seelhöfer, Lennart von Werder, Dennis Greiwede   #
#===================================================#
"""

# Django standard imports
from django.db import models
from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

# Standard modules
import datetime
import sys
sys.path.append("..")

# File imports
from sprinkler.controller.interface import *

# Other modules
import pytz # Python Timezone module

# Status Choices for Plans & Devices
STATUS_CHOICES = [
    ('OK', 'OK'),
    ('Warnung', 'Warnung'),
    ('Fehler', 'Fehler'),
]


class CommonInfo(models.Model):
    """This contains common info (attributes and functions) other models can inherit from."""
    name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='OK',
    )

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Device(CommonInfo):
    """This class is the abstraction layer for all hardware devices."""
    contr_id = models.IntegerField() # Controller ID
    device_type = None
    device_type_id = None

    class Meta:
        abstract = True


# Pump Model
class Pump(Device):
    """Representation of the pump which valves can attach to."""
    curr_active = models.BooleanField(default=False)
    device_type = 'Pump'
    flow_capacity = models.DecimalField(max_digits=5, decimal_places=2) # Maximum flow capacity the pump can make work
    current_workload = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def activate(self):
        """Activate sets current status to on and initiates message to the controller."""
        if self.curr_active == False:
            self.curr_active = True
            self.save()
            set_pump(str(self.contr_id), "ON")

    def deactivate(self):
        """Deactivate sets current status to off, turns off all attached valves and initiates message to the controller."""
        if self.curr_active == True:
            self.curr_active = False
            self.save()
            set_pump(str(self.contr_id), "OFF")
            attached_valves = self.get_attached_valves()
            for valve in attached_valves:
                valve.deactivate()

    def get_attached_valves(self):
        return Valve.objects.filter(pump_fk__exact=self)

    def add_to_current_workload(self, add_value):
        """
        Value gets add to current workload.  
        
        If the workload results in a value greater than 0 the pump gets turned on.
        """
        self.current_workload += add_value
        self.save()
        if self.current_workload > 0:
            self.activate()

    def subtract_from_current_workload(self, subtract_value):
        """
        Value gets subtracted from current workload.  
        
        If the workload results in a value equal to 0 the pump gets turned off.
        """
        self.current_workload -= subtract_value
        self.save()
        if self.current_workload == 0:
            self.deactivate()


class PumpForm(forms.ModelForm):
    """Model form for the Pump model"""
    def __init__(self, *args, **kwargs):
        super(PumpForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })

    class Meta:
        model = Pump
        fields = ['name', 'contr_id', 'flow_capacity']
        labels = {
        'name': 'Name der Pumpe', 
        'contr_id': 'Controller ID', 
        'flow_capacity': 'Durchflussmenge in L/min'
        }


class Sensor(Device):
    """This represents a humidity sensor which is connected to one or more valves."""
    curr_active = models.BooleanField(default=False)
    device_type = 'Sensor'
    moisture = models.DecimalField(max_digits=5, decimal_places=2, default=0)


class SensorForm(forms.ModelForm):
    """Model form for the Sensor model"""
    def __init__(self, *args, **kwargs):
        super(SensorForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })

    class Meta:
        model = Sensor
        fields = ['name', 'contr_id']
        labels = {
        'name': 'Name des Sensors', 
        'contr_id': 'Controller ID'
        }


class Valve(Device):
    """
    This represents the connection in between one pump and one to many sprinklers.  
    
    A valve can be opened or closed which results in either all attached sprinklers being
    turned on of none.
    """
    curr_active = models.BooleanField(default=False)
    device_type = 'Ventil'
    valve_counter = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    watering_time = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sensor_fk = models.ForeignKey(Sensor, on_delete=models.SET_NULL, blank=True, null=True)
    pump_fk = models.ForeignKey(Pump, on_delete=models.SET_NULL, null=True)

    activate_date_time = models.DateTimeField(blank=True, null=True) # Stores this information for the entry in the logging table (WateringStatistic model)

    def activate(self):
        """Sets currently active to on, adds the workload of the attached sprinklers to the pump workload and activates the sprinklers."""
        if self.curr_active == False:
            self.pump_fk.add_to_current_workload(self.get_attached_flow_capacity())
            self.curr_active = True
            self.activate_date_time = timezone.now()
            self.save()
            set_valve(str(self.contr_id), "ON")
    
    def deactivate(self):
        """Sets currently active to off, subtracts the workload of the attached sprinklers form the pump and deactivates the sprinklers."""
        if self.curr_active == True:
            self.pump_fk.subtract_from_current_workload(self.get_attached_flow_capacity())
            self.curr_active = False
            time_difference = timezone.now() - self.activate_date_time
            WateringStatistic.objects.create(start_time=self.activate_date_time, valve_fk=self, duration_seconds=time_difference.total_seconds())
            self.activate_date_time = None
            self.save()
            set_valve(str(self.contr_id), "OFF")

    def get_attached_sprinklers(self):
        return Sprinkler.objects.filter(valve_fk__exact=self)

    def get_attached_flow_capacity(self):
        attached_flow_capacity = 0
        attached_valves = self.get_attached_sprinklers()
        for valve in attached_valves:
            attached_flow_capacity += valve.flow_capacity
        return attached_flow_capacity


class ValveForm(forms.ModelForm):
    """Model form for the Valve model"""
    def __init__(self, *args, **kwargs):
        super(ValveForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if Valve._meta.get_field(field).get_internal_type() == 'BooleanField':
                self.fields[field].widget.attrs.update({    
                    'class': 'form-check'
                })
            else:
                self.fields[field].widget.attrs.update({    
                    'class': 'form-control'
                })
        

    class Meta:
        model = Valve
        fields = ['name', 'contr_id', 'sensor_fk', 'pump_fk']
        labels = {
        'name': 'Name des Ventils', 
        'contr_id': 'Controller ID', 
        'sensor_fk': 'Zugehöriger Sensor', 
        'pump_fk': 'Zugehörige Pumpe'
        }


# Sprinkler Model
class Sprinkler(Device):
    """This represents the last object in the chain after the pump and the valve."""
    curr_active = models.BooleanField(default=False)
    device_type = 'Sprinkler'
    flow_capacity = models.DecimalField(max_digits=5, decimal_places=2)

    # Sprinkler weiterhin gespeichert, wenn ein Ventil geloescht wird, damit es bei Bedarf einen anderen Ventil zugeordnet werden kann
    valve_fk = models.ForeignKey(Valve, on_delete=models.SET_NULL, null=True)


# Form for Sprinkler
class SprinklerForm(forms.ModelForm):
    """Model form for the Sprinkler model"""
    def __init__(self, *args, **kwargs):
        super(SprinklerForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })

    class Meta:
        model = Sprinkler
        fields = ['name', 'contr_id', 'flow_capacity', 'valve_fk']
        labels = {
        'name': 'Name des Sprinklers', 
        'contr_id': 'Controller ID', 
        'flow_capacity': 'Durchflusskapzität in L/min', 
        'valve_fk': 'Zugehöriges Ventil'
        }


class WeatherCounter(models.Model):
    weather_counter = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def modify_weather_counter(self):
        automatic_plan = self.get_activ_automatic_plan()
        if automatic_plan is not None:
            if not automatic_plan.automation_sensor:
                counter = self.weather_counter
                if automatic_plan.automation_rain:
                    # * 1/4 , da es vier mal pro Stunde aufgerufen wird (beim Update des Wetters)
                    counter = counter + self.get_rain() * (1/4)
                if automatic_plan.automation_temperature:
                    # * 1/4 , da es vier mal pro Stunde aufgerufen wird (beim Update des Wetters)
                    counter = counter + self.get_temperature() * (1/4)
                self.weather_counter = counter
                self.save()

    def is_sensor_activ(self):
        # Placeholder for the check if a sensor is active
        return False

    def get_rain(self):
        rain_counter = 0 # self.get_current_rain_data(maria_db_connection) # Abfrage ergaenzen

        if rain_counter >= 20:
            return -100
        elif rain_counter > 0:
            return rain_counter * (-5)
        else:
            return 0

    # Werte noch anpassen
    def get_temperature(self):
        temperature_counter = 0 # self.get_current_temperature(marida_db_connection) # Abfrage an Model
        if 0 <= temperature_counter <= 10:
            return 1
        elif 10 < temperature_counter <= 15:
            return 3 / 2
        elif 15 < temperature_counter <= 20:
            return 2
        elif 20 < temperature_counter <= 25:
            return 5 / 2
        elif temperature_counter >= 25:
            return 3
        else:
            return 0

    def get_activ_automatic_plan(self):
        plans = Plan.objects.filter(is_active_plan=True)
        for plan in plans:
            if plan.automation_rain or plan.automation_sensor or plan.automation_temperature:
                return plan
        return None

    def reset_weather_counter(self):
        self.weather_counter = 0
        self.save()


class Plan(CommonInfo):
    """
    This represents a plan a user can create.  
    
    A plan can either be an automatic plan or a manual plan.  
    When its a manual plan the user can define certain time intervals (ref. Schedule model) in which the plan should be executed.  
    When its an automatic plan the application itself calculates based on different inputs when the garden needs to be watered.
    """
    is_active_plan = models.BooleanField(default=False)
    description = models.CharField(max_length=3000)

    valve_threshold = models.IntegerField(default=100)
    moisture_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=100)

    automation_rain = models.BooleanField(default=False)
    timespace_rain_forecast = models.IntegerField(default=24) # Standardwert 24h für forecast beachten
    automation_sensor = models.BooleanField(default=False)
    automation_temperature = models.BooleanField(default=False)

    # Relationen zu Ventilen
    valve = models.ManyToManyField(Valve)

    next_execution_time = None

    def get_related_schedules(self):
        return self.schedule_set.all()
    
    def activate(self):
        """Deactivates all plans and afterwards activates self"""
        if self.is_active_plan == False:
            plans = Plan.objects.all()
            for plan in plans:
                plan.deactivate()
                plan.save()
            transfer_plan(self)
            self.is_active_plan = True
            self.save()
    
    def deactivate(self):
        if self.is_active_plan == True:
            delete_plan()
            self.is_active_plan = False
            self.save()

    def get_next_allowed_start_date_time(self):
        """Gets the datetime objects based on all related Schedule objects."""
        next_allowed_start_date_time = None
        if self.is_active_plan:
            schedules = self.get_related_schedules()
            for schedule in schedules:
                if schedule.is_allow:
                    schedule_next_date_time = schedule.get_next_date_time(schedule.get_weekdays(),
                                                                                schedule.time_start)
                    if (next_allowed_start_date_time == None) or (
                            next_allowed_start_date_time > schedule_next_date_time):
                        next_allowed_start_date_time = schedule_next_date_time
        return next_allowed_start_date_time
    
    def get_next_denied_start_date_time(self):
        """Gets the datetime objects based on all related Schedule objects."""
        next_denied_start_date_time = None
        if self.is_active_plan:
            schedules = self.get_related_schedules()
            if schedules.first() is None:
                return None
            for schedule in schedules:
                if schedule.is_deny:
                    schedule_next_date_time = schedule.get_next_date_time(schedule.get_weekdays(),
                                                                                schedule.time_start)
                    if (next_allowed_start_date_time == None) or (
                            next_allowed_start_date_time > schedule_next_date_time):
                        next_allowed_start_date_time = schedule_next_date_time
        return next_allowed_start_date_time
    
    def is_allow_time(self):
        """It is an allowed time if none of the associated Schedules is a denied time window and at least one of the Schedules is in an allowed time window."""
        schedules = self.get_related_schedules()
        if schedules.first() is None:
            return True
        for schedule in schedules:
            allow_time = False
            if schedule.is_denied_time():
                return False
            if schedule.is_allowed_time():
                allow_time = True
        return allow_time


class PlanForm(forms.ModelForm):
    """Model form for the Plan model"""
    def __init__(self, *args, **kwargs):
        super(PlanForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if Plan._meta.get_field(field).get_internal_type() == 'BooleanField':
                self.fields[field].widget.attrs.update({    
                    'class': 'form-check'
                })
            else:
                self.fields[field].widget.attrs.update({    
                    'class': 'form-control'
                })

    class Meta:
        model = Plan
        fields = ['name', 'description', 'valve_threshold', 'moisture_threshold', 'automation_rain', 'timespace_rain_forecast', 'automation_sensor', 'automation_temperature', 'valve']
        labels = {
        "name": "Name des Plans",
        'description': "Beschreibung", 
        'valve_threshold': "Aktivierungsschwelle des Ventils", 
        'moisture_threshold': "Aktivierungsschwelle des Feuchtigkeitssensors", 
        'automation_rain': "Automatisierung durch Regendaten", 
        'timespace_rain_forecast': "Reichweite in Tagen der Regengestützten Automatisierung", 
        'automation_sensor': "Auswahl des Sensors", 
        'automation_temperature': "Automatisierung durch Temperatur", 
        'valve': "Ventile (Mehrere durch STRG+Klick auswählbar)"
        }

class Schedule(models.Model):
    """
    This model is always linked to a Plan object.  
    
    A schedule can define either an allowed or a denied time window. 
    """
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)

    is_deny = models.BooleanField(default=False)
    is_allow = models.BooleanField(default=False)

    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    time_start = models.TimeField(auto_now=False, auto_now_add=False)
    time_stop = models.TimeField(auto_now=False, auto_now_add=False)

    weekdays = None
    next_start_date_time = None
    next_end_date_time = None
    next_denied_start_date_time = None
    next_denied_end_date_time = None

    def get_next_date_time(self, weekdays, dt):
        """This is a helper function which returns the next datetime at which a time window in this schedule is met."""
        weekday = datetime.datetime.now().weekday()

        for i in range(0, 8):
            if weekday in weekdays:
                now_date_time = datetime.datetime.now()
                temp_date_time = now_date_time + datetime.timedelta(days=i)

                day = str("{:02d}".format(temp_date_time.day))
                month = str("{:02d}".format(temp_date_time.month))
                year = str(temp_date_time.year)
                hour = str("{:02d}".format(dt.hour))
                minute = str("{:02d}".format(dt.minute))
                second = str("{:02d}".format(dt.second))

                date_time_str = year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + second
                date_time = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')

                if date_time > now_date_time:
                    return date_time

            if weekday == 6:
                weekday = 0
            else:
                weekday += 1

    def get_weekdays(self):
        weekdays = []
        if self.monday: weekdays.append(0)
        if self.tuesday: weekdays.append(1)
        if self.wednesday: weekdays.append(2)
        if self.thursday: weekdays.append(3)
        if self.friday: weekdays.append(4)
        if self.saturday: weekdays.append(5)
        if self.sunday: weekdays.append(6)
        return weekdays

    def is_allowed_time(self):
        if self.is_allow:
            next_start_date_time = self.get_next_date_time(self.get_weekdays(), self.time_start)
            next_end_date_time = self.get_next_date_time(self.get_weekdays(), self.time_stop)
            if next_start_date_time != None:
                is_same_day = next_start_date_time <= next_end_date_time
            else:
                return False

            if is_same_day:
                return False
            else:
                return True
        else:
            return False

    def is_denied_time(self):
        if self.is_deny:
            next_start_date_time = self.get_next_date_time(self.get_weekdays(), self.time_start)
            next_end_date_time = self.get_next_date_time(self.get_weekdays(), self.time_stop)
            if next_start_date_time != None:
                is_same_day = next_start_date_time <= next_end_date_time
            else:
                return False

            if is_same_day:
                return False
            else:
                return True
        else:
            return False


class ScheduleForm(forms.ModelForm):
    """Model form for the Schedule model"""
    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })

    class Meta:
        model = Schedule
        fields = ['is_allow', 'is_deny', 'plan', 'monday', 'tuesday', 'wednesday', 'thursday',
                  'friday', 'saturday', 'sunday', 'time_start', 'time_stop']
        labels = {
        "is_allow": "Zeitplan für erlaubten Zeitraum",
        "is_deny": "Zeitplan für verbotenen Zeitraum",
        "monday": "Montag", 
        "tuesday": "Dienstag", 
        "wednesday": "Mittwoch", 
        "thursday": "Donnerstag",
        "friday": "Freitag", 
        "saturday": "Samstag", 
        "sunday": "Sonntag", 
        "time_start": "Startzeit", 
        "time_stop": "Stoppzeit",
        }

class Location(models.Model):
    """This represents a location. The main purpose is to save location meta data to display it in the frontend."""
    city = models.CharField(max_length=200, blank=True)
    town = models.CharField(max_length=200, blank=True)
    village = models.CharField(max_length=200, blank=True)
    municipality = models.CharField(max_length=200, blank=True)
    county = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    utc_offset = models.IntegerField(blank=True)
    latitude = models.DecimalField(max_digits=7, decimal_places=5)
    longitude = models.DecimalField(max_digits=7, decimal_places=5)

    def __str__(self):
        """Creates the string which is displayed different frontend locations"""
        name = ''
        if self.city != '':
            name = name + self.city + ', '
        if self.town != '':
            name = name + self.town + ', '
        if self.village != '':
            name = name + self.village + ', '
        if self.municipality != '':
            name = name + self.municipality + ', '
        if self.county != '':
            name = name + self.county + ', '
        if self.state != '':
            name = name + self.state + ', '
        if self.country != '':
            name = name + self.country
        return name


class WeatherStatus(models.Model):
    """
    This model represents a weather status from the OWM-Weather status.  
    
    The objects of this models are static and will not be changed during runtime.
    """
    owm_id = models.IntegerField()
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=128)
    icon = models.CharField(max_length=3)

    def __str__(self):
        return str(self.owm_id)


class WeatherData(models.Model):
    """This represents a weather status at a certain time."""
    reference_time = models.DateTimeField()
    last_update_time = models.DateTimeField()
    reception_time = models.DateTimeField()
    location_fk = models.ForeignKey(Location, on_delete=models.CASCADE)
    humidity = models.IntegerField()
    pressure = models.IntegerField()
    rain = models.DecimalField(max_digits=4, decimal_places=2)
    temperature = models.DecimalField(max_digits=4, decimal_places=2)
    wind = models.DecimalField(max_digits=4, decimal_places=2)

    weather_status_fk = models.ForeignKey(WeatherStatus, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.last_update_time = datetime.datetime.now()
        super().save(*args, **kwargs)


class UserSettings(models.Model):
    """This is used to store user-based data."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    owm_api_key = models.CharField(max_length=32, blank=True)


class WateringStatistic(models.Model):
    """
    This is a logging model.  
    
    A new object of this model is created every time a valve gets turned off.
    """
    start_time = models.DateTimeField()
    valve_fk = models.ForeignKey(Valve, on_delete=models.SET_NULL, null=True)
    duration_seconds = models.DecimalField(max_digits=5, decimal_places=2)
    water_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Calculates the water amount which was used during this time the valve was turned on.
        try:
            flow_capacity = self.valve_fk.get_attached_flow_capacity()
            self.water_amount = float(self.duration_seconds) / float(60) * float(flow_capacity)
        except:
            pass

    def get_water_amount(self):
        return self.water_amount