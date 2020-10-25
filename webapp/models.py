from django.db import models
from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User

import datetime

# Status Choices for Plans & Devices
STATUS_CHOICES = [
    ('OK', 'OK'),
    ('Warnung', 'Warnung'),
    ('Fehler', 'Fehler'),
]


class CommonInfo(models.Model):
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
    contr_id = models.IntegerField()
    device_type = None
    device_type_id = None 

    class Meta:
        abstract = True


# Pump Model
class Pump(Device):
    curr_active = models.BooleanField(default=False)
    device_type = 'Pump'
    flow_capacity = models.DecimalField(max_digits=5, decimal_places=2)
    current_workload = models.DecimalField(max_digits=5, decimal_places=2, default=0)


class PumpForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PumpForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })

    class Meta:
        model = Pump
        fields = ['name', 'contr_id', 'flow_capacity']


class Sensor(Device):
    curr_active = models.BooleanField(default=False)
    device_type = 'Sensor'
    moisture = None


class SensorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SensorForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })

    class Meta:
        model = Sensor
        fields = ['name', 'contr_id']


class Valve(Device):
    curr_active = models.BooleanField(default=False)
    device_type = 'Ventil'
    valve_counter = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    watering_time = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sensor_fk = models.ForeignKey(Sensor, on_delete=models.SET_NULL, blank=True, null=True)
    pump_fk = models.ForeignKey(Pump, on_delete=models.SET_NULL, null=True)


class ValveForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ValveForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })

    class Meta:
        model = Valve
        fields = ['name', 'contr_id', 'sensor_fk', 'pump_fk']


# Sprinkler Model
class Sprinkler(Device):
    curr_active = models.BooleanField(default=False)
    device_type = 'Sprinkler'
    flow_capacity = models.DecimalField(max_digits=5, decimal_places=2)

    # Sprenkler weiterhin gespeichert, wenn ein Ventil geloescht wird, damit es bei Bedarf einen anderen Ventil zugeordnet werden kann
    valve_fk = models.ForeignKey(Valve, on_delete=models.SET_NULL, null=True) 

# Form for Sprinkler
class SprinklerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SprinklerForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })

    class Meta:
        model = Sprinkler
        fields = ['name', 'contr_id', 'flow_capacity', 'valve_fk']


class WeatherCounter(models.Model):
    weather_counter = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def modify_weather_counter(self):
        automatic_plan = self.get_activ_automatic_plan()
        if automatic_plan is not None:
            if not automatic_plan.automation_sensor:   # Platzhalter, noch aendern
                counter = self.weather_counter
                if automatic_plan.automation_rain:
                    counter = counter + self.get_rain()
                if automatic_plan.automation_temperature:
                    counter = counter + self.get_temperature()
                self.weather_counter = counter
                self.save()

    # Platzhalter zur Pruefung, ob ein Sensor aktiv ist
    def is_Sensor_activ(self):
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
            return 0
        elif 10 < temperature_counter <= 15:
            return 1 / 8
        elif 15 < temperature_counter <= 20:
            return 1 / 6
        elif 20 < temperature_counter <= 25:
            return 1 / 3
        elif temperature_counter >= 25:
            return 1 / 2
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

    def get_related_pumps(self):
        return self.pump.all()

    def is_current_time_denied(self):
        return True

    def get_next_allowed_start_date_time(self):
        next_allowed_start_date_time = None
        schedules = self.get_related_schedules()
        for schedule in schedules:
            schedule_next_allowed_date_time = schedule.get_next_date_time(schedule.get_allowed_weekdays(),
                                                                          schedule.allow_time_start)
            if (next_allowed_start_date_time == None) or (
                    next_allowed_start_date_time > schedule_next_allowed_date_time):
                next_allowed_start_date_time = schedule_next_allowed_date_time
        return next_allowed_start_date_time

    def get_next_denied_start_date_time(self):
        next_denied_start_date_time = None
        schedules = self.get_related_schedules()
        for schedule in schedules:
            schedule_next_denied_start_date_time = schedule.get_next_date_time(schedule.get_denied_weekdays(),
                                                                               schedule.deny_time_start)
            if (next_denied_start_date_time == None) or (
                    next_denied_start_date_time > schedule_next_denied_start_date_time):
                next_denied_start_date_time = schedule_next_denied_start_date_time
        return next_denied_start_date_time

    def get_next_allowed_end_date_time(self):
        next_allowed_start_date_time = None
        schedules = self.get_related_schedules()
        for schedule in schedules:
            schedule_next_allowed_date_time = schedule.get_next_date_time(schedule.get_allowed_weekdays(),
                                                                          schedule.allow_time_stop)
            if (next_allowed_start_date_time == None) or (
                    next_allowed_start_date_time > schedule_next_allowed_date_time):
                next_allowed_start_date_time = schedule_next_allowed_date_time
        return next_allowed_start_date_time

    def get_next_denied_end_date_time(self):
        next_denied_start_date_time = None
        schedules = self.get_related_schedules()
        for schedule in schedules:
            schedule_next_denied_start_date_time = schedule.get_next_date_time(schedule.get_denied_weekdays(),
                                                                               schedule.deny_time_stop)
            if (next_denied_start_date_time == None) or (
                    next_denied_start_date_time > schedule_next_denied_start_date_time):
                next_denied_start_date_time = schedule_next_denied_start_date_time
        return next_denied_start_date_time

    def get_pumps_to_be_activated(self):
        schedules = self.get_related_schedules()
        pumps_to_be_activated = None
        is_denied_time = False
        for schedule in schedules:
            if schedule.is_denied_time():
                return None
            elif schedule.is_allowed_time():
                pumps_to_be_activated = self.get_related_pumps()
        return pumps_to_be_activated



class PlanForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PlanForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
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
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)

    allow_monday = models.BooleanField(default=False)
    allow_tuesday = models.BooleanField(default=False)
    allow_wednesday = models.BooleanField(default=False)
    allow_thursday = models.BooleanField(default=False)
    allow_friday = models.BooleanField(default=False)
    allow_saturday = models.BooleanField(default=False)
    allow_sunday = models.BooleanField(default=False)
    allow_time_start = models.TimeField(auto_now=False, auto_now_add=False)
    allow_time_stop = models.TimeField(auto_now=False, auto_now_add=False)

    deny_monday = models.BooleanField(default=False)
    deny_tuesday = models.BooleanField(default=False)
    deny_wednesday = models.BooleanField(default=False)
    deny_thursday = models.BooleanField(default=False)
    deny_friday = models.BooleanField(default=False)
    deny_saturday = models.BooleanField(default=False)
    deny_sunday = models.BooleanField(default=False)
    deny_time_start = models.TimeField(auto_now=False, auto_now_add=False)
    deny_time_stop = models.TimeField(auto_now=False, auto_now_add=False)

    allowed_weekdays = None
    denied_weekdays = None
    next_allowed_start_date_time = None
    next_allowed_end_date_time = None
    next_denied_start_date_time = None
    next_denied_end_date_time = None

    def get_next_date_time(self, weekdays, dt):
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

    def get_allowed_weekdays(self):
        allowed_weekdays = []
        if self.allow_monday: allowed_weekdays.append(0)
        if self.allow_tuesday: allowed_weekdays.append(1)
        if self.allow_wednesday: allowed_weekdays.append(2)
        if self.allow_thursday: allowed_weekdays.append(3)
        if self.allow_friday: allowed_weekdays.append(4)
        if self.allow_saturday: allowed_weekdays.append(5)
        if self.allow_sunday: allowed_weekdays.append(6)
        return allowed_weekdays

    def get_denied_weekdays(self):
        denied_weekdays = []
        if self.deny_monday: denied_weekdays.append(0)
        if self.deny_tuesday: denied_weekdays.append(1)
        if self.deny_wednesday: denied_weekdays.append(2)
        if self.deny_thursday: denied_weekdays.append(3)
        if self.deny_friday: denied_weekdays.append(4)
        if self.deny_saturday: denied_weekdays.append(5)
        if self.deny_sunday: denied_weekdays.append(6)
        return denied_weekdays

    def is_allowed_time(self):
        next_allowed_start_date_time = self.get_next_date_time(self.get_allowed_weekdays(), self.allow_time_start)
        next_allowed_end_date_time = self.get_next_date_time(self.get_allowed_weekdays(), self.allow_time_stop)
        if next_allowed_start_date_time != None:
            is_same_day = next_allowed_start_date_time <= next_allowed_end_date_time
        else:
            return False

        if is_same_day:
            return False
        else:
            return True

    def is_denied_time(self):
        next_denied_start_date_time = self.get_next_date_time(self.get_denied_weekdays(), self.deny_time_start)
        next_denied_end_date_time = self.get_next_date_time(self.get_denied_weekdays(), self.deny_time_stop)
        if next_denied_start_date_time != None:
            is_same_day = next_denied_start_date_time <= next_denied_end_date_time
        else:
            return False

        if is_same_day:
            return False
        else:
            return True


class ScheduleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })

    class Meta:
        model = Schedule
        fields = ['plan', 'allow_monday', 'allow_tuesday', 'allow_wednesday', 'allow_thursday',
                  'allow_friday', 'allow_saturday', 'allow_sunday', 'allow_time_start', 'allow_time_stop',
                  'deny_monday', 'deny_tuesday', 'deny_wednesday', 'deny_thursday',
                  'deny_friday', 'deny_saturday', 'deny_sunday', 'deny_time_start', 'deny_time_stop']

class Location(models.Model):
    """ Location Model """
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
    """ WeatherStatus Model """
    owm_id = models.IntegerField()
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=128)
    icon = models.CharField(max_length=3)

    def __str__(self):
        return str(self.owm_id)


class WeatherData(models.Model):
    """ WeatherData Model """
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
    """ UserSettings Model """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    owm_api_key = models.CharField(max_length=32, blank=True)