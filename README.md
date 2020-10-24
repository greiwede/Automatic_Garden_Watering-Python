# python-sprinkler

Python Sprinkler is a Django based application for managing and controlling sprinklers in your garden.
It is supposed to run on a Raspberry Pi.

## Setup

How to setup a working Sprinkler application.

### Raspbian
1. Install Python3.*, RabbitMQ and libATLAS for Celery\
<pre>pi@raspberry:~ $ <b>sudo apt-get install python3 rabbitmq-server libatlas-base-dev</b></pre>
2. Create Virtual Environment\
<pre>$  python3 -m venv sprinklerenv</pre>
3. Change Directory\
<pre>cd spinklerenv</pre>
4. Activate Virtual Environment\
<pre>$ source bin/activate</pre>
5. Clone Repository\
<pre>git clone https://github.com/lennartvonwerder/python-sprinkler.git</pre>
6. Change Directory\
<pre>cd python-sprinkler</pre>
7. Install all required Python modules\
<pre>$ pip install -U -r requirements.txt</pre>
8. Start Server\
<pre>$ python manage.py runserver</pre>

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
