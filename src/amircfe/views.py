import pathlib
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from visits.models import PageVisit
from django.conf import settings

LOGIN_URL = settings.LOGIN_URL

this_dir = pathlib.Path(__file__).resolve().parent


def home_view(request, *args, **kwargs):
    # FIXED: Removed the print statement that was crashing for logged-out users
    return about_view(request, *args, **kwargs)


def about_view(request, *args, **kwargs):
    qs = PageVisit.objects.all()
    page_qs = PageVisit.objects.filter(path=request.path)
    try:
        percent = (page_qs.count() * 100) / qs.count()
    except:
        percent = 0
    my_title = "My page"
    my_context = {
        "page_title": my_title,
        "percent": percent,
        "page_visit_count": page_qs.count(),
        "total_visit_count": qs.count(),
    }
    path = request.path
    html_template = "home.html"
    PageVisit.objects.create(path=request.path)
    return render(request, html_template, my_context)


VALID_CODE = "abc123"

def pw_protected_view(request, *args, **kwargs):
    is_allowed = request.session.get('protected_page_allowed') or 0
    print(request.session.get('protected_page_allowed'), type (request.session.get('protected_page_allowed')))
    if request.method == "POST":
        user_pw_sent = request.POST.get("code") or None
        if user_pw_sent == VALID_CODE:
            is_allowed = 1
            request.session['protected_page_allowed'] = is_allowed
    if  is_allowed:
        return render(request, "protected/view.html",{})
    return render(request, "protected/entry.html",{})


@login_required
def user_only_view(request,*args, **kwargs):
    print(request.user.is_staff)
    return render(request, "protected/user-only.html")

@staff_member_required(login_url=LOGIN_URL)
def staff_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html")