# python-sprinkler

Python Sprinkler is a Django based application for managing and controlling sprinklers in your garden.
It is supposed to run on a Raspberry Pi.

<h2>Setup</h2>

How to setup a working Sprinkler application.<br>
<br>

<h4>Raspbian</h4>
<ol>
	<li>Install Python: apt-get install python3</li>
	<li>Create Virtual Environment: virtualenv -p python3 sprinklerenv</li>
	<li>Activate Virtual Environment: source bin/activate</li>
	<li>Install Python in Virtual Environment: apt-get install python3</li>
	<li>Install Python-Django: python -m pip install Django</li>
	<li>Install Django Crontab Module: pip install django-crontab</li>
	<li>Install Python Localization Module: pip install geopy</li>
	<li>Clone Repository: git clone https://github.com/lennartvonwerder/python-sprinkler.git</li>
	<li>Change Directory: cd python-spinkler</li>
	<li>Start Server: python manage.py runserver</li>
</ol>

<h4>Windows</h4>
<ol>
	<li>Install Python https://www.python.org/downloads/</li>
	<li>Create Virtual Environment: virtualenv -p python3 sprinklerenv</li>
	<li>Activate Virtual Environment: source bin/activate</li>
	<li>Install Python-Django: python -m pip install Django</li>
	<li>Install Django Crontab Module: pip install django-crontab</li>
	<li>Install Python Localization Module: pip install geopy</li>
	<li>Clone Repository: git clone https://github.com/lennartvonwerder/python-sprinkler.git</li>
	<li>Change Directory: cd python-spinkler</li>
	<li>Start Server: python manage.py runserver</li>
</ol>

<h4>Login:</h4>
Username: sprinkleradmin<br>
Password: admin1234!#<br>

<h2>How this project was created</h2>

This project was established as an exam for the module "Programmierprojekt".
