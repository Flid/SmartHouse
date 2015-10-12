# -*- coding: utf-8 -*-
from ..base import BaseTemplateView


class MainPageView(BaseTemplateView):
    def get(self):
        return self.render_to_response('index.html')
