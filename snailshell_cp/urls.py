from django.contrib import admin
from django.urls import path

from snailshell_cp import views

urlpatterns = [
    path('create_deploy_job/', views.create_deploy_job),
    path('', admin.site.urls),
]
