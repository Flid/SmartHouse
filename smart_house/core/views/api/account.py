# -*- coding: utf-8 -*-


from . import forms
from ..base import BaseView


class LoginOccupationView(BaseView):
    #basic_form = forms.LoginOccupationForm

    def post(self):
        self.process_basic_form()
        login = self.form_values['login']
        user = User.load(login=login, assert_exists=False) if login else None
        return JsonRenderer(occupied=(user is not None))

