# -*- encoding: utf-8 -*-

from django.urls import path
from .views import login_view, salir
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', login_view, name="login"),
    path('salir/', salir, name="exit"),
]
