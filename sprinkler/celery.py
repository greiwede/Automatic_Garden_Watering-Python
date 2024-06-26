"""
#===================================================#
#                  celery.py                        #
#===================================================#
#  Diese Datei entählt die grundlegenden            #
#  Einstellungen fuer Celery und die Terminierung   #
#  der regelmäßig ausgefuehrten Aufgaben            #
#===================================================#
# Entwickler : Dennis Greiwe                        #
#===================================================#
"""
import os

from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sprinkler.settings')

app = Celery('sprinkler')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'manual_irrigation':{
        'task': 'sprinkler.tasks.manual_irrigation',
        'schedule': crontab(minute='*/1')
    },
    'read_weather':{
        'task': 'sprinkler.tasks.read_weather',
        'schedule': crontab(minute='*/15')
    },
    'automatic_irrigation':{
        'task': 'sprinkler.tasks.aut_irrigation',
        'schedule': crontab(minute='*/15')
    }
}

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')