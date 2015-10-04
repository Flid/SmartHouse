# -*- coding: utf-8 -*-
from wtforms import (
    Form,
    StringField,
    PasswordField,
    validators,
)


class RegistrationForm(Form):
    username = StringField(validators=[
        validators.DataRequired(),
        validators.Length(min=4, max=25),
    ])
    password = PasswordField(validators=[
        validators.DataRequired(),
        validators.EqualTo('password_confirmation', message='Passwords must match'),
    ])
    password_confirmation = PasswordField(validators=[
        validators.DataRequired(),
    ])

    email = StringField(validators=[
        validators.DataRequired(),
        validators.Email(),
    ])

    display_name = StringField(validators=[
        validators.Length(min=4, max=25),
    ])


class LoginForm(Form):
    username = StringField(validators=[
        validators.DataRequired(),
        validators.Length(min=4, max=25),
    ])
    password = PasswordField(validators=[
        validators.DataRequired(),
    ])
