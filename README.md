# python-sprinkler

Python Sprinkler is a Django based application for managing and controlling sprinklers in your garden.
It is supposed to run on a Raspberry Pi.

## Setup

How to setup a working Sprinkler application.

### Raspbian
1. Install Python: `$ apt-get install python3`
2. Create Virtual Environment: `$ virtualenv -p python3 sprinklerenv`
3. Activate Virtual Environment: `$ source bin/activate`
4. Install Python in Virtual Environment: `$ apt-get install python3`
5. `$ apt-get install rabbitmq-server`
6. Clone Repository: `git clone https://github.com/lennartvonwerder/python-sprinkler.git`
7. Change Directory: `cd python-spinkler`
8. Install all required Python modules: `$ pip install -U -r requirements.txt`
9. Start Server: `$ python manage.py runserver`

### Windows
1. Install Python https://www.python.org/downloads/
2. Create Virtual Environment: py -m venv env
3. Activate Virtual Environment: .\env\Scripts\activate
4. Clone Repository: `git clone https://github.com/lennartvonwerder/python-sprinkler.git`
5. Change Directory: `cd python-spinkler`
6. Install all required Python modules: `pip install -U -r requirements.txt`
7. Start Server: `python manage.py runserver`

##### Login:
Username: `sprinkleradmin`
Password: `admin1234!#`

## How this project was created

This project was established as an exam for the module "Programmierprojekt".
