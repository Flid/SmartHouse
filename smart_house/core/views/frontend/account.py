# -*- coding: utf-8 -*-
import logging

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout, login
from django.shortcuts import redirect

from smart_house.core import exceptions
from smart_house.core import models


from . import forms
from ..base import BaseTemplateView
from .. import helpers


logger = logging.getLogger('views.frontend')


class LoginView(BaseTemplateView):
    basic_form = forms.LoginForm

    def get(self):
        return self.render_to_response('account/login.html')

    def post(self):
        self.process_basic_form()

        user = authenticate(
            username=self.form_values['username'],
            password=self.form_values['password'],
        )

        if user is None:
            raise exceptions.PasswordInvalid()

        login(self.request, user)

        return self.render_redirect('fe:index')


class LogoutView(BaseTemplateView):
    def post(self):
        logout(self.request)
        return self.render_redirect('fe:index')


class SettingsView(BaseTemplateView):

    def get(self):
        return self.render_to_response(
            'account/settings.html',
            context=dict(
                show_saved_message=self.request.GET.get('status') == 'saved',
            ),
        )

__all__ = (
    'LoginView',
    'LoginOccupationView',
    'LogoutView',
    'SettingsView',
)

