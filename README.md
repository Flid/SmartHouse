## Installation

Install all the packages needed: python3-virtualenv python3-dev postgresql-9.1 postgresql-server-dev-9.1

virtualenv -p python3 ve
. ./ve/bin/activate

pip install requirements.txt`

Setup postgres:

"CREATE USER pi WITH PASSWORD 'megapassword';"
"CREATE DATABASE smart_house_local;"


Generate static:
sudo mkdir /var/www/smart_house
./manage.py collectstatic --settings smart_house.settings.prod
sudo chown nginx:nginx /var/www/smart_house/ -R
