#!/usr/bin/env sh
set -e

python manage.py collectstatic --noinput

if [ "$(echo "$DEBUG" | awk '{print tolower($0)}')" =  "true" ]
then
    python manage.py runserver 0.0.0.0:8000
else
    uwsgi --ini $ROOT/uwsgi.ini
fi
