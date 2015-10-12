# -*- coding: utf-8 -*-
from wtforms import (
    Form,
    StringField,
    PasswordField,
    validators,
)

class LoginForm(Form):
    username = StringField(validators=[
        validators.DataRequired(),
        validators.Length(min=4, max=25),
    ])
    password = PasswordField(validators=[
        validators.DataRequired(),
    ])
