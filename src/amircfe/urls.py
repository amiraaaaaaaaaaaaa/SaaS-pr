"""
URL configuration for amircfe project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from .views import (home_view,
                    about_view,
                    pw_protected_view,
                     user_only_view,
                    staff_only_view)


urlpatterns = [
    path('', home_view, name='home'),
    path('hello-world/', home_view),
    # allauth owns authentication; these keep the old URLs working.
    path('login/', RedirectView.as_view(pattern_name='account_login', permanent=False)),
    path("register/", RedirectView.as_view(pattern_name='account_signup', permanent=False)),
    path("about/", about_view),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path("protected/", pw_protected_view),
    path('protected/user-only/' , user_only_view),
    path('protected/staff-only/' , staff_only_view),
    path('profiles/', include('profiles.urls')),#for accounts login and signing up
    path('home_page/', home_view),
]
