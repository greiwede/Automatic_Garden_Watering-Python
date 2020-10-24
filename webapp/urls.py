from django.urls import path
from django.contrib import admin
from . import views


urlpatterns = [
    
    # Index
    path('', views.index, name='index'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Devices
    path('devices/', views.devices, name='devices'),
    path('devices/start/<int:device_type>/<int:device_id>', views.device_start, name='device_start'),
    path('devices/stop/<int:device_type>/<int:device_id>', views.device_stop, name='device_stop'),   
    path('devices/create/<int:device_type>', views.device_create, name='device_create'),
    path('devices/edit/<int:device_type>/<int:device_id>', views.device_edit, name='device_edit'),
    path('devices/delete/<int:device_type>/<int:device_id>', views.device_delete, name='device_delete'),
    
    # Plans
    path('plans/', views.plans, name='plans'),
    path('plans/create', views.plans_create, name='plan_create'),
    path('plans/edit/<int:plan_id>', views.plans_edit, name='plan_edit'),
    path('plans/delete/<int:plan_id>', views.plans_delete, name='plan_delete'),

    # Schedules (in Plans)
    path('plans/edit/<int:plan_id>/schedule/create/', views.schedule_create, name='schedule_create'),
    path('plans/edit/<int:plan_id>/schedule/edit/<int:schedule_id>', views.schedule_edit, name='schedule_edit'),
    path('plans/edit/<int:plan_id>/schedule/delete/<int:schedule_id>', views.schedule_delete, name='schedule_delete'),

    # Statistics
    path('statistics/', views.statistics, name='statistics'),
    path('statistics/<int:year>/', views.statistics, name='statistics_year'),

    # Weather
    path('weather/', views.weather, name='weather'),

    # Settings
    path('settings/', views.settings, name='settings'),

    # Help
    path('help/', views.help, name='help'),

    # Admin
    path('admin/logout/', views.logout_view, name='logout'),
    path('admin/', admin.site.urls),
    
]