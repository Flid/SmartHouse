# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin
from smart_house.core.views import frontend, api
from smart_house.core.views.frontend.main import MainPageView


fe_account_urls = [
    url(r'^login$', frontend.account.LoginView.as_view(), name='login'),
    url(r'^logout$', frontend.account.LogoutView.as_view(), name='logout'),
    url(r'^settings$', frontend.account.SettingsView.as_view(), name='settings'),
]

frontend_urls = [
    url(r'^$', frontend.main.MainPageView.as_view(), name='index'),
    url(r'^sensors$', frontend.main.SensorsView.as_view(), name='sensors'),
    url(r'^account/', include(fe_account_urls, namespace='account')),
]

api_account_urls = [
    url(r'^login_occupation$', api.account.LoginOccupationView.as_view(), name='login_occupation'),
]

api_urls = [
    url(r'^account/', include(api_account_urls, namespace='account')),
]

urlpatterns = [
    url(r'^', include(frontend_urls, namespace='fe')),
    url(r'^', include(api_urls, namespace='api')),
]
