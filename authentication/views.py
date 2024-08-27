from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from django.http import  JsonResponse, HttpResponse, HttpResponseBadRequest
from django.contrib.auth.models import User
import secrets
import random
import json


def login_view(request):

    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                msg = 'Invalid credentials'
                print(msg)
        else:
            msg = 'Error validating the form'
            print(msg)

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


def salir(request):
    logout(request)
    return redirect("/")