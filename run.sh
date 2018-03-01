#!/usr/bin/env sh

python manage.py collectstatic --noinput

python manage.py migrate --noinput

python manage.py initialize

if [ "$(echo "$DEBUG" | awk '{print tolower($0)}')" =  "true" ]
then
    python manage.py runserver 0.0.0.0:8000
else
    uwsgi --ini $ROOT/uwsgi.ini
fi
