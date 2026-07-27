"""Legacy hand-rolled auth, superseded by django-allauth.

Not routed any more -- /login/ and /register/ redirect to allauth's
account_login / account_signup. Kept for reference only; if you ever re-enable
these, note the templates post allauth's field names (login, password1).
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django.contrib.auth import get_user_model

User = get_user_model()


def login_view(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("login") or None
        password = request.POST.get("password") or None

        if all([username, password]):
            user = authenticate(request, username=username, password = password)
            if user is not None:
                login(request,user)
                return redirect("/home_page/")
        error = "Invalid username or password."

    return render(request, "auth/login.html", {"error": error})

def register_view(request):
    errors = []
    if request.method == "POST":
        username = request.POST.get("username") or None
        password = request.POST.get("password1") or None
        email = request.POST.get("email") or None

        if not username:
            errors.append("Username is required.")
        if not password:
            errors.append("Password is required.")
        if username and User.objects.filter(username__iexact=username).exists():
            errors.append("That username is already taken.")
        if email and User.objects.filter(email__iexact=email).exists():
            errors.append("That email is already registered.")

        if password and not errors:
            try:
                validate_password(password)
            except ValidationError as e:
                errors.extend(e.messages)

        if not errors:
            User.objects.create_user(username, email=email, password=password)
            return redirect("/login/")

    return render(request, "auth/register.html", {"errors": errors})
