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
<pre>pi@raspberry:~ $ <b>sudo apt-get install python3 python3-venv python2.7 curl git rabbitmq-server libatlas-base-dev</b></pre>
2. Enable serial communication of the Raspberry Pi
    1. Enter the following command
    <pre>pi@raspberry:~ $ <b>sudo raspi-config</b></pre>
    2. Use the arrow keys to get to option 5 Interfacing Options and hit Enter
    3. In the next menu navigate to P6 Serial and hit Enter again
    4. Accept the next question by hitting Enter when Yes is selected
    5. Confirm the dialog by hitting Enter on the OK button and navigate to the Finish button on the next menu and hit Enter.
    6. Reboot the Raspberry Pi
    <pre>pi@raspberry:~ $ <b>sudo reboot</b></pre>
3. Create Virtual Environment
<pre>pi@raspberry:~ $ <b>python3 -m venv sprinklerenv</b></pre>
4. Change Directory
<pre>pi@raspberry:~ $ <b>cd sprinklerenv</b></pre>
5. Activate Virtual Environment
<pre>pi@raspberry:~ $ <b>source bin/activate</b></pre>
6. Clone Repository
<pre>pi@raspberry:~ $ <b>git clone https://github.com/lennartvonwerder/python-sprinkler.git</b></pre>
7. Change Directory
<pre>pi@raspberry:~ $ <b>cd python-sprinkler</b></pre>
8. Install all required Python modules
<pre>pi@raspberry:~ $ <b>pip install -r requirements.txt</b></pre>
9. Start Server
    - Only available at localhost (http://localhost:8000/ or http://127.0.0.1:8000/)
    <pre>pi@raspberry:~ $ <b>python manage.py runserver</b></pre>
    - Available at localhost and externally at IP of the network device (http://localhost:8000/ or http://127.0.0.1:8000/ or http://{IP-Address}:8000/)
        1. Add the devices IP address to the `ALLOWED_HOSTS` list in `sprinkler/settings.py`.
        2. <pre>pi@raspberry:~ $ <b>python manage.py runserver 0.0.0.0:8000</b></pre>
10. Enjoy!

### Windows

Make sure to use the Windows Command Prompt, PowerShell is not supported. We also want to state that under Windows Celery is not supported which means that all background jobs like automatic/manual watering as well as periodic weather updates will not work.

1. Install Python: https://www.python.org/downloads/
2. Create Virtual Environment
<pre>python -m venv sprinklerenv</pre>
3. Change Directory
<pre>cd sprinklerenv</pre>
4. Activate Virtual Environment
<pre>Scripts\activate.bat</pre>
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
