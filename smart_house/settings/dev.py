# -*- coding: utf-8 -*-
from .base import *

SECRET_KEY = 'verysecretkey'
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'smart_house_dev',
        'USER': 'pi',
        'PASSWORD': 'megapassword',
        'HOST': 'localhost',
        'PORT': '5432',
    },
}
