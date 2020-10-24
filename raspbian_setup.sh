#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "Please run as root (sudo)"
  exit
fi

# update package list
echo -e "\e[93mUpdating package list\033[0m"
apt-get update
echo -e "\e[92mPackage list updated successfully\033[0m"

# install required packages
echo -e "\e[93mInstalling required packages\033[0m"
apt-get install python3 rabbitmq-server libatlas-base-dev -y
echo -e "\e[92mFinished installing required packages\033[0m"

# create virtual environment
echo -e "\e[93mEnter name for virtual environment (default: sprinklerenv): \033[0m"
read venvname
if [ -z "$venvname" ] 
then 
    venvname="sprinklerenv"
fi 
echo -e "\e[93mSetting up venv '$venvname"
python3 -m venv sprinklerenv
cd sprinklerenv
source bin/activate

# clone repository
git clone https://github.com/lennartvonwerder/python-sprinkler.git
cd python-sprinkler

# install required pip modules
echo -e "\e[93mInstall required pip modules\033[0m"
pip install -r requirements.txt
echo -e "\e[92mFinished installing required pip modules\033[0m"

# finished
echo -e "\e[42mInstallation finished successfully\033[0m"
echo -e "\e[93mTo start the server simply type: python manage.py runserver\033[0m"