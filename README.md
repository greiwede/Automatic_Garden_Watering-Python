# python-sprinkler

Python Sprinkler is a Django based application for managing and controlling sprinklers in your garden.
It is supposed to run on a Raspberry Pi.

## Setup

How to setup a working Sprinkler application.

### Raspbian
1. Install Python3.*, RabbitMQ and libATLAS for Celery\
<pre>pi@raspberry:~ $ <b>sudo apt-get install python3 rabbitmq-server libatlas-base-dev</b></pre>
2. Create Virtual Environment\
<pre>pi@raspberry:~ $ <b>python3 -m venv sprinklerenv</b></pre>
3. Change Directory\
<pre>pi@raspberry:~ $ <b>cd spinklerenv</b></pre>
4. Activate Virtual Environment\
<pre>pi@raspberry:~ $ <b>source bin/activate</b></pre>
5. Clone Repository\
<pre>pi@raspberry:~ $ <b>git clone https://github.com/lennartvonwerder/python-sprinkler.git</b></pre>
6. Change Directory\
<pre>pi@raspberry:~ $ <b>cd python-sprinkler</b></pre>
7. Install all required Python modules\
<pre>pi@raspberry:~ $ <b>pip install -U -r requirements.txt</b></pre>
8. Start Server\
<pre>pi@raspberry:~ $ <b>python manage.py runserver</b></pre>

### Windows
1. Install Python: https://www.python.org/downloads/\
2. Create Virtual Environment\
`py -m venv sprinklerenv`
3. Change Directory\
`cd spinklerenv`
4. Activate Virtual Environment\
`.\env\Scripts\activate`
5. Clone Repository\
`git clone https://github.com/lennartvonwerder/python-sprinkler.git`
6. Change Directory\
`cd python-sprinkler`
7. Install all required Python modules\
`pip install -U -r requirements.txt`
8. Start Server\
`python manage.py runserver`

##### Login:
Username: `sprinkleradmin`\
Password: `admin1234!#`

## How this project was created
This project was established as an exam for the module "Programmierprojekt".
