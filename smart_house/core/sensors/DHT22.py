# -*- coding: utf-8 -*-

import sys
import logging
from time import sleep
from django.conf import settings
from threading import Thread

temperature = None
humidity = None

DHT22_GPIO_NUMBER = 24

errors_count = 0
errors_threshold = 10

log = logging.getLogger(__name__)


def background_task():
    global temperature, humidity, errors_count
    import Adafruit_DHT

    while True:
        # Try to grab a sensor reading.  Use the read_retry method which will retry up
        # to 15 times to get a sensor reading (waiting 2 seconds between each retry).
        _humidity, _temperature = Adafruit_DHT.read_retry(
            Adafruit_DHT.DHT22,
            DHT22_GPIO_NUMBER,
        )

        # Un-comment the line below to convert the temperature to Fahrenheit.
        # temperature = temperature * 9/5.0 + 32

        # Note that sometimes you won't get a reading and
        # the results will be null (because Linux can't
        # guarantee the timing of calls to read the sensor).
        # If this happens try again!
        if _humidity is not None and _temperature is not None:
            print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(_temperature, _humidity))
            temperature = _temperature
            humidity = _humidity
        else:
            print('Failed to get reading. Try again!')
            errors_count += 1
            if errors_count > errors_threshold:
                temperature = None
                humidity = None

        sleep(10)



if settings.SENSORS.get('DHT22', {}).get('enabled'):
    Thread(target=background_task).start()
