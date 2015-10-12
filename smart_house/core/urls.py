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
    url(r'^account/', include(fe_account_urls, namespace='account')),
]

api_service_urls = [
    url('^update$', api.service.UpdateView.as_view(), name='update')
]

api_urls = [
    url(r'^service/', include(api_service_urls, namespace='service')),
]

urlpatterns = [
    url(r'^', include(frontend_urls, namespace='fe')),
    url(r'^api/', include(api_urls, namespace='api')),
]
