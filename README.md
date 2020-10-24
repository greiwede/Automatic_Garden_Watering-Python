# python-sprinkler

Python Sprinkler is a Django based application for managing and controlling sprinklers in your garden.
It is supposed to run on a Raspberry Pi.

## Setup

How to setup a working Sprinkler application.

### Raspbian
1. Install Python3*, RabbitMQ and libATLAS for Celery: `$ apt-get install python3 rabbitmq-server libatlas-base-dev`
2. Create Virtual Environment: `$  python3 -m venv sprinklerenv`
3. Change Directory: `cd spinklerenv`
4. Activate Virtual Environment: `$ source bin/activate`
5. Clone Repository: `git clone https://github.com/lennartvonwerder/python-sprinkler.git`
6. Change Directory: `cd python-spinkler`
7. Install all required Python modules: `$ pip install -U -r requirements.txt`
8. Start Server: `$ python manage.py runserver`

### Windows
1. Install Python https://www.python.org/downloads/
2. Create Virtual Environment: `py -m venv sprinklerenv`
3. Change Directory: `cd spinklerenv`
4. Activate Virtual Environment: `.\env\Scripts\activate`
5. Clone Repository: `git clone https://github.com/lennartvonwerder/python-sprinkler.git`
6. Change Directory: `cd python-spinkler`
7. Install all required Python modules: `pip install -U -r requirements.txt`
8. Start Server: `python manage.py runserver`

##### Login:
Username: `sprinkleradmin`
Password: `admin1234!#`

## How this project was created

This project was established as an exam for the module "Programmierprojekt".
