# python-sprinkler

Python Sprinkler is a Django based application for managing and controlling sprinklers in your garden.
It is supposed to run on a Raspberry Pi.

## Setup

How to setup a working Sprinkler application.

### Raspbian
#### Option 1: automatic setup via setup script
1. Download setup script and execute
<pre>pi@raspberry:~ $ <b>sudo bash <(curl -s https://raw.githubusercontent.com/lennartvonwerder/python-sprinkler/master/raspbian_setup.sh)</b></pre>
2. Enjoy!

#### Option 2: manual setup
1. Install Python3.*, RabbitMQ and libATLAS for Celery
<pre>pi@raspberry:~ $ <b>sudo apt-get install python3 python3-venv curl git rabbitmq-server libatlas-base-dev</b></pre>
2. Create Virtual Environment
<pre>pi@raspberry:~ $ <b>python3 -m venv sprinklerenv</b></pre>
3. Change Directory
<pre>pi@raspberry:~ $ <b>cd spinklerenv</b></pre>
4. Activate Virtual Environment
<pre>pi@raspberry:~ $ <b>source bin/activate</b></pre>
5. Clone Repository
<pre>pi@raspberry:~ $ <b>git clone https://github.com/lennartvonwerder/python-sprinkler.git</b></pre>
6. Change Directory
<pre>pi@raspberry:~ $ <b>cd python-sprinkler</b></pre>
7. Install all required Python modules
<pre>pi@raspberry:~ $ <b>pip install -r requirements.txt</b></pre>
8. Start Server
<pre>pi@raspberry:~ $ <b>python manage.py runserver</b></pre>
9. Enjoy!

### Windows
1. Install Python: https://www.python.org/downloads/
2. Create Virtual Environment
<pre>py -m venv sprinklerenv</pre>
3. Change Directory
<pre>cd spinklerenv</pre>
4. Activate Virtual Environment
Windows Command Prompt:<pre>Scripts\activate.bat</pre>
Windows PowerShell:<pre>Scripts\activate.ps1</pre>
5. [Download latest release](https://github.com/lennartvonwerder/python-sprinkler/releases/latest), unzip it and place the folder into the current directory
6. Enter the code directory
<pre>cd python-sprinkler</pre>
7. Install all required Python modules
<pre>pip install -r requirements.txt</pre>
8. Start Server
<pre>python manage.py runserver</pre>
9. Enjoy!

##### Login:
Username: `sprinkleradmin`\
Password: `admin1234!#`

## How this project was created
This project was established as an exam for the module "Programmierprojekt".
