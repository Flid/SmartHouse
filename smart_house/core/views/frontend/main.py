# -*- coding: utf-8 -*-
from ..base import BaseTemplateView
from smart_house.core.sensors import DHT22


class MainPageView(BaseTemplateView):
    def get(self):
        return self.render_to_response('index.html')


class SensorsView(BaseTemplateView):
    def get(self):
        return self.render_to_response(
            'sensors.html',
            {
                'humidity': DHT22.humidity,
                'temperature': DHT22.temperature,
            }
        )
