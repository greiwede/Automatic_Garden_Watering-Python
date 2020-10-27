"""
#===================================================#
#                   views.py                        #
#===================================================#
#  This file contains functions that make the       #
#  webapp work.                                     #
#===================================================#
# Developers: Malte Seelhöfer, Lennart von Werder   #
#===================================================#
"""

from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.template import Context, loader
from django.template.response import TemplateResponse
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
import sys
sys.path.append("..")
from .models import *
from sprinkler.controller.interface import *
from sprinkler.tasks import read_weather
import json
from geopy.geocoders import Nominatim
from pyowm.owm import OWM
from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder
from pytz import timezone, utc


# Displays the index page. Redirects the user if signed in.
def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    template = loader.get_template("index.html")
    return HttpResponse(template.render())

@login_required(login_url='/admin/login/')
def dashboard(request):
    # Display the dashboard page. Login required.
    args = {}   
    # Read user config from config file
    args['first_name'] = request.user.first_name.capitalize()    
    # Get next watering time data
    plans = Plan.objects.all()
    next_allowed_start_date_time = None
    for plan in plans:
        plan_next_allowed_start_date_time = plan.get_next_allowed_start_date_time()
        if next_allowed_start_date_time == None:
            next_allowed_start_date_time = plan_next_allowed_start_date_time
        elif plan_next_allowed_start_date_time == None:
            continue
        elif next_allowed_start_date_time > plan_next_allowed_start_date_time:
            next_allowed_start_date_time = plan_next_allowed_start_date_time
    if next_allowed_start_date_time != None:
        args['water_time_year'] = str(next_allowed_start_date_time.year)
        args['water_time_month'] = str("{:02d}".format(next_allowed_start_date_time.month))
        args['water_time_day'] = str("{:02d}".format(next_allowed_start_date_time.day))
        args['water_time_hour'] = str("{:02d}".format(next_allowed_start_date_time.hour))
        args['water_time_minute'] = str("{:02d}".format(next_allowed_start_date_time.minute))
    # Get location data
    try:
        loc = Location.objects.all()[:1][0]
        if loc.city != '':
            args['location_town'] = loc.city    
        elif loc.town != '':
            args['location_town'] = loc.town
        elif loc.village != '':
            args['location_town'] = loc.village
        elif loc.municipality != '':
            args['location_town'] = loc.municipality
        if loc.county != '':
            args['location_county'] = loc.county
        if loc.state != '':
            args['location_state'] = loc.state
        if loc.country != '':
            args['location_country'] = loc.country
    except:
        pass
    try:
        weather = WeatherData.objects.latest('reference_time')
        args['temperature'] = weather.temperature
        weather_status = weather.weather_status_fk
        args['weather_status'] = weather_status.description
        args['weather_status_icon'] = weather_status.icon
        # Get time of day
        hour = datetime.now().hour
        if hour <= 8 or hour >= 21:
            args['daytime'] = 'n' # Night
        else:
            args['daytime'] = 'd' # Day    
        # Get greeting
        if ( hour >= 0 and hour < 6 ) or ( hour > 20 and hour <= 23 ):
            args['greeting'] = "Guten Abend"
        elif hour >= 6 and hour < 10:
            args['greeting'] = "Guten Morgen"
        elif hour >= 13 and hour < 15:
            args['greeting'] = "Guten Mittag"
        else:
            args['greeting'] = "Guten Tag"
    except:
        pass
    args['water_amount'] = 0
    ws_amount = WateringStatistic.objects.filter(start_time__gte=datetime.now()-timedelta(days=7))
    for ws in ws_amount:
        args['water_amount'] += ws.get_water_amount()
    # Returns the corresponding template including the arguments.
    return TemplateResponse(request, "dashboard.html", args)

@login_required(login_url='/admin/login/')
def devices(request):
    # Shows the devices (sprinkler, sensors, pumps, valves). Login Required.
    # Edit Key: Defines the type of device for editing, controlling or deleting.
    # The edit key is used in other views as well.
    # Sprinkler = 0
    # Sensor = 1
    # Pumpe = 2
    # Ventil = 3 
    args = {}
    # GET variables of the filter (filter by name).
    args['filter_name'] = request.GET.get('name', '')
    args['filter_device'] = request.GET.get('device', '')
    args['filter_status'] = request.GET.get('status', '')
    # Parameter that checks whether a filter is activated
    check = 0
    # Switch statement to show the right type of device.
    if args['filter_device'] == 'Ventil':
        devices = Valve.objects
        args['edit_key'] = 3
        args['type_name'] = 'valve'
    elif args['filter_device'] == 'Pumpe':
        devices = Pump.objects
        args['edit_key'] = 2
        args['type_name'] = 'pump'
    elif args['filter_device'] == 'Sensor':
        devices = Sensor.objects
        args['edit_key'] = 1
        args['type_name'] = 'sensor'
    elif args['filter_device'] == 'Sprinkler':
        devices = Sprinkler.objects
        args['edit_key'] = 0
        args['type_name'] = 'sprinkler'  
    elif args['filter_device'] == '':
        devices = Sprinkler.objects
        args['edit_key'] = 0
        args['filter_device'] = 'Sprinkler'
        args['type_name'] = 'sprinkler'
    # If a filter is set, the filtering happens next:
    if args['filter_name'] != '':
        devices = devices.filter(name__contains=args['filter_name'])
        check = 1
    if args['filter_status'] == 'OK' or args['filter_status'] == 'Warnung' or args['filter_status'] == 'Fehler':
        devices = devices.filter(status__contains=args['filter_status'])
        check = 1
    # If no filter is activated all the devices of the choosen type are collected.
    if(check == 0):
        devices = devices.all()
    args['devices'] = devices
    # Renders the corresponding template.
    return TemplateResponse(request, "devices.html", args)


@login_required(login_url='/admin/login/')
def device_start(request, device_type, device_id):
    # Starts a device (Valves & Pumps only). Login Required.
    args = {}
    # Switch statement to identify the device type (edit key)
    if device_type == 2:
        pump = Pump.objects.get(id=device_id)
        pump.activate() # Activation method
        print('Pumpe mit der ID ', device_id, ' wurde gestartet.')
        return redirect('/devices/?device=Pumpe')
    elif device_type == 3:
        valve = Valve.objects.get(id=device_id)
        valve.activate() # Activation method
        print('Ventil mit der ID ', device_id, ' wurde gestartet.')
        return redirect('/devices/?device=Ventil')
    # Redirects to the devices page.
    return redirect('devices')

@login_required(login_url='/admin/login/')
def device_stop(request, device_type, device_id):
    # Stops a device (Valves & Pumps only).
    args = {}
    # Switch statement to identify the device type (edit key)
    if device_type == 2:
        pump = Pump.objects.get(id=device_id)
        pump.deactivate()
        print('Pumpe mit der ID ', device_id, ' wurde gestoppt.')
        return redirect('/devices/?device=Pumpe')
    elif device_type == 3:
        valve = Valve.objects.get(id=device_id)
        valve.deactivate()
        print('Ventil mit der ID ', device_id, ' wurde gestoppt.')
        return redirect('/devices/?device=Ventil')

    return redirect('devices')

@login_required(login_url='/admin/login/')
def device_create(request, device_type):
    # Creates and saves a new device
    args = {}
    args['device_type'] = device_type

    if device_type == 0: # Sprinkler
        if request.method == 'POST':
            d = SprinklerForm(request.POST)
            new_device = d.save()
            return redirect('devices')
        else:
            args['headline'] = "Neuer Sprinkler"
            args['form'] = SprinklerForm()
    elif device_type == 1: # Sensor
        if request.method == 'POST':
            d = SensorForm(request.POST)
            new_device = d.save()
            return redirect('/devices/?device=Sensor')
        else:
            args['headline'] = "Neuer Sensor"
            args['form'] = SensorForm()
    elif device_type == 2: # Pump
        if request.method == 'POST':
            d = PumpForm(request.POST)
            new_device = d.save()
            return redirect('/devices/?device=Pumpe')
        else:
            args['headline'] = "Neue Pumpe"
            args['form'] = PumpForm()
    elif device_type == 3: # Valve
        if request.method == 'POST':
            d = ValveForm(request.POST)
            new_device = d.save()
            return redirect('/devices/?device=Ventil')
        else:
            args['headline'] = "Neues Ventil"
            args['form'] = ValveForm()

    return TemplateResponse(request, "device_create.html", args)

@login_required(login_url='/admin/login/')
def device_edit(request, device_type, device_id):
    # Lets the user edit a device.
    args = {}
    args['device_type'] = device_type
    args['device_id'] = device_id

    if device_type == 0: # Sprinkler
        if request.method == 'POST':
            d = Sprinkler.objects.get(pk=device_id)
            f = SprinklerForm(request.POST, instance=d)
            f.save()
            return redirect('devices')
        else:
            d = Sprinkler.objects.get(pk=device_id)
            args['headline'] = "Sprinkler bearbeiten"
            args['form'] = SprinklerForm(instance=d)
        
    elif device_type == 1: # Sensor
        if request.method == 'POST':
            d = Sensor.objects.get(pk=device_id)
            f = SensorForm(request.POST, instance=d)
            f.save()
            return redirect('/devices/?device=Sensor')
        else:
            d = Sensor.objects.get(pk=device_id)
            args['headline'] = "Sensor bearbeiten"
            args['form'] = SensorForm(instance=d)
        
    elif device_type == 2: # Pump
        if request.method == 'POST':
            d = Pump.objects.get(pk=device_id)
            f = PumpForm(request.POST, instance=d)
            f.save()
            return redirect('/devices/?device=Pumpe')
        else:
            d = Pump.objects.get(pk=device_id)
            args['headline'] = "Pumpe bearbeiten"
            args['form'] = PumpForm(instance=d)
    elif device_type == 3: # Valve
        if request.method == 'POST':
            d = Valve.objects.get(pk=device_id)
            f = ValveForm(request.POST, instance=d)
            f.save()
            return redirect('/devices/?device=Ventil')
        else:
            d = Valve.objects.get(pk=device_id)
            args['headline'] = "Ventil bearbeiten"
            args['form'] = ValveForm(instance=d)  

    return TemplateResponse(request, "device_edit.html", args)

@login_required(login_url='/admin/login/')
def device_delete(request, device_type, device_id):
    # Lets the user delete a device
    args = {}

    if device_type == 0:
        Sprinkler.objects.get(id=device_id).delete()
        return redirect('/devices/?device=Sprinkler')
    elif device_type == 1:
        Sensor.objects.get(id=device_id).delete()
        return redirect('/devices/?device=Sensor')
    elif device_type == 2:
        Pump.objects.get(id=device_id).delete()
        return redirect('/devices/?device=Pumpe')
    elif device_type == 3:
        Valve.objects.get(id=device_id).delete()
        return redirect('/devices/?device=Ventil')

    return redirect('devices')

@login_required(login_url='/admin/login/')
def plans(request):
    # Shows all plans
    args = {}
    args['filter_name'] = request.GET.get('name', '')
    args['filter_status'] = request.GET.get('status', '')

    plans = Plan.objects

    check = 0

    if(args['filter_name'] != ''):
        plans = plans.filter(name__contains=args['filter_name'])
        check = 1
    elif(args['filter_status'] == 'OK' or args['filter_status'] == 'Warnung' or args['filter_status'] == 'Fehler'):
        plans = plans.filter(status__contains=args['filter_status'])
        check = 1

    if(check == 0):
        plans = plans.all()

    for plan in plans:
        plan.next_execution_time = plan.get_next_allowed_start_date_time()

    args['plans'] = plans

    return TemplateResponse(request, "plans.html", args)

@login_required(login_url='/admin/login/')
def plans_create(request):
    # Lets the user create and save a new plan
    args = {}
    args['form'] = PlanForm()
    # If there are POST values, the plan is getting saved, and the user will be redirected to edit page.
    if request.method == 'POST':
        plan_form = PlanForm(request.POST)
        new_plan = plan_form.save()
        return redirect('plan_edit', new_plan.id)

    return TemplateResponse(request, "plans_create.html", args)

@login_required(login_url='/admin/login/')
def plans_activate(request, plan_id):
    # Activate a plan (only one plan can be active)
    plan = Plan.objects.get(pk=plan_id)
    plan.activate()
    return redirect('plans')

@login_required(login_url='/admin/login/')
def plans_deactivate(request, plan_id):
    # Deactivates a plan
    plan = Plan.objects.get(pk=plan_id)
    plan.deactivate()
    return redirect('plans')

@login_required(login_url='/admin/login/')
def plans_edit(request, plan_id):
    # Lets the user edit an existing plan.
    args = {}
    args['id'] = plan_id

    if request.method == 'POST':
        plan = Plan.objects.get(pk=plan_id)
        plan_form = PlanForm(request.POST, instance=plan)
        plan_form.save()
        return redirect('plans')
    else:
        plan = Plan.objects.get(pk=plan_id)
        args['form'] = PlanForm(instance=plan)

        schedules = Schedule.objects.filter(plan=plan_id).all()
        for schedule in schedules:
            if schedule.is_allow:
                schedule.weekdays = schedule.get_weekdays()
                next_allowed_start_date_time = schedule.get_next_date_time(schedule.weekdays, schedule.time_start)
                next_allowed_end_date_time = schedule.get_next_date_time(schedule.weekdays, schedule.time_stop)
            if schedule.is_deny:
                schedule.weekdays = schedule.get_weekdays()
                next_denied_start_date_time = schedule.get_next_date_time(schedule.weekdays, schedule.time_start)
                next_denied_end_date_time = schedule.get_next_date_time(schedule.weekdays, schedule.time_stop)

        args['schedules'] = schedules

    return TemplateResponse(request, "plans_edit.html", args)

@login_required(login_url='/admin/login/')
def plans_delete(request, plan_id):
    # Deletion of a plan
    plan = Plan.objects.get(id=plan_id)
    plan.delete()
    return redirect('plans')

@login_required(login_url='/admin/login/')
def schedule_create(request, plan_id):
    # Create and save a new schedule inside a plan
    args = {}
    args['form'] = ScheduleForm(initial={'plan': plan_id})
    args['plan'] = Plan.objects.get(pk=plan_id)

    if request.method == 'POST':
        schedule_form = ScheduleForm(request.POST)
        new_schedule = schedule_form.save()
        return redirect('plan_edit', plan_id=plan_id)

    return TemplateResponse(request, "schedule_create.html", args)

@login_required(login_url='/admin/login/')
def schedule_edit(request, plan_id, schedule_id):
    # Edit and save the schedule
    args = {}
    args['id'] = plan_id
    args['plan'] = Plan.objects.get(pk=plan_id)
    args['schedule_id'] = schedule_id

    if request.method == 'POST':
        schedule = Schedule.objects.get(pk=schedule_id)
        schedule_form = ScheduleForm(request.POST, instance=schedule)
        schedule_form.save()
        return redirect('plan_edit', plan_id=plan_id)
    else:
        schedule = Schedule.objects.get(pk=schedule_id)
        args['form'] = ScheduleForm(instance=schedule)

    return TemplateResponse(request, "schedule_edit.html", args)

@login_required(login_url='/admin/login/')
def schedule_delete(request, plan_id, schedule_id):
    # Delete a schedule
    Schedule.objects.filter(id=schedule_id, plan=plan_id).delete()
    return redirect('plan_edit', plan_id=plan_id)

@login_required(login_url='/admin/login/')
def statistics(request, year=int(datetime.now().strftime('%Y'))):
    # Shows the statistics of a choosen year to the user.
    args = {}
    args['year'] = year
    args['year_before'] = year + 1
    args['year_after'] = year - 1

    ws_year = WateringStatistic.objects.filter(start_time__year=year)

    for i in range(1, 13):
        ws_month = ws_year.filter(start_time__month=i)
        args['water_month_' + str(i)] = 0
        for ws in ws_month:
            args['water_month_' + str(i)] += ws.get_water_amount()
    
    args['watering_statistics'] = WateringStatistic.objects.filter(start_time__gte=datetime.now()-timedelta(days=14))
    
    return TemplateResponse(request, "statistics.html", args)

@login_required(login_url='/admin/login/')
def weather(request):
    # The weather page
    args = {}

    try:
        loc = Location.objects.all()[:1][0]
        args['location_name'] = loc.__str__()
    except:
        pass

    weathers = WeatherData.objects.all()
    args['weathers'] = weathers

    # Get time of day
    hour = datetime.now().hour
    if hour <= 8 or hour >= 21:
        args['daytime'] = 'n' # Night
    else:
        args['daytime'] = 'd' # Day

    return TemplateResponse(request, "weather.html", args)

@login_required(login_url='/admin/login/')
def settings(request):
    # Settings page
    def get_location_data(lat, lon, loc):
        """ Get location name data and utc offset and set it in the model """
        lat = float(lat)
        lon = float(lon)

        loc.latitude = lat
        loc.longitude = lon

        # Get location name data and set it in the model
        try:
            geolocator = Nominatim(user_agent="openmapquest", timeout=3)
            location = geolocator.reverse('{}, {}'.format(lat, lon), language='de')
            address = address = location.raw['address']
        except:
            address = {}

        if 'city' in address:
            loc.city = address['city']    
        elif 'town' in address:
            loc.town = address['town']
        elif 'village' in address:
            loc.village = address['village']
        elif 'municipality' in address:
            loc.municipality = address['municipality']
        if 'county' in address:
            loc.county = address['county']
        if 'state' in address:
            loc.state = address['state']
        if 'country' in address:
            loc.country = address['country']
        
        # Get UTC offset of the location
        today = datetime.now()
        tf = TimezoneFinder()
        tz_target = timezone(tf.certain_timezone_at(lat=lat, lng=lon))
        today_target = tz_target.localize(today)
        today_utc = utc.localize(today)
        loc.utc_offset = int((today_utc - today_target).total_seconds() / 3600)

        return loc

    # Start of main functionality
    args = {}

    request_latitude = request.POST.get('latitude')
    request_longitude = request.POST.get('longitude')

    if request_latitude == None or request_longitude == None:
        # When attributes are not given
        try:
            loc = Location.objects.all()[:1][0]
            
            args['filter_latitude'] = str(loc.latitude)
            args['filter_longitude'] = str(loc.longitude)
            args['location_name'] = loc.__str__()
        except:
            args['filter_latitude'] = ''
            args['filter_longitude'] = ''
    elif request_latitude == '' and request_longitude == '':
        # No Location given. Delete existing Location and empty fiels
        print("no location given")
        try:
            loc = Location.objects.all()[:1][0]
            loc.delete()
        except:
            pass
        args['filter_latitude'] = request_latitude
        args['filter_longitude'] = request_longitude
    elif request_latitude == '' or request_longitude == '' or float(request_latitude) < -90 or float(request_latitude) > 90 or float(request_longitude) < -180 or float(request_longitude) > 180:
        # Invalid Coordinates
        args['error'] = "Eingegebene Koordinaten fehlerhaft."

        args['filter_latitude'] = request_latitude
        args['filter_longitude'] = request_longitude
    else:
        # If location exists get it - otherwise create one
        try:
            loc = Location.objects.all()[:1][0]
            loc.delete()
            
            loc = get_location_data(request_latitude, request_longitude, Location())
            loc.save()
            read_weather()
        except:
            loc = get_location_data(request_latitude, request_longitude, Location())
            loc.save()
            read_weather()
        args['filter_latitude'] = str(loc.latitude)
        args['filter_longitude'] = str(loc.longitude)
        args['location_name'] = loc.__str__()
    
    # API-Key Settings
    if request.POST.get('owmAPIKey') == None:
        user = User.objects.get(username__exact=request.user.username)
        if hasattr(user, 'usersettings'):
            args['filter_owm_api_key'] = user.usersettings.owm_api_key
        else:
            args['filter_owm_api_key'] = ''

    elif request.POST.get('owmAPIKey') == '':
        user = User.objects.get(username__exact=request.user.username)
        if hasattr(user, 'usersettings'):
            user_settings = user.usersettings
            user_settings.owm_api_key = ''
            user_settings.save() 
        args['filter_owm_api_key'] = ''
    else:
        try:
            user = User.objects.get(username__exact=request.user.username)
            if hasattr(user, 'usersettings'):
                user_settings = user.usersettings
                user_settings.owm_api_key = request.POST.get('owmAPIKey')
                user_settings.save() 
            else:
                user_settings = UserSettings.objects.create(user=user, owm_api_key=request.POST.get('owmAPIKey'))
                user.save()
            args['filter_owm_api_key'] = user_settings.owm_api_key
        except:
            args['filter_owm_api_key'] = ''

    args['username'] = request.user.username
    args['first_name'] = request.user.first_name
    
    return TemplateResponse(request, "settings.html", args)


def help(request):
    # Displays the help page.
    args = {}
    return TemplateResponse(request, "help.html", args)

def logout_view(request):
    # Signs out the user and redirects to the index view
    logout(request)
    return redirect('/')