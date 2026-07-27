from decouple import config
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from visits.models import PageVisit
from django.conf import settings

LOGIN_URL = settings.LOGIN_URL


def home_view(request, *args, **kwargs):
    return about_view(request, *args, **kwargs)


def about_view(request, *args, **kwargs):
    PageVisit.objects.create(path=request.path)

    total_count = PageVisit.objects.count()
    page_count = PageVisit.objects.filter(path=request.path).count()
    percent = (page_count * 100) / total_count if total_count else 0

    my_context = {
        "page_title": "My page",
        "percent": percent,
        "page_visit_count": page_count,
        "total_visit_count": total_count,
    }
    return render(request, "home.html", my_context)


VALID_CODE = config("PROTECTED_PAGE_CODE", cast=str, default="abc123")

def pw_protected_view(request, *args, **kwargs):
    is_allowed = request.session.get('protected_page_allowed') or 0
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
    return render(request, "protected/user-only.html")

@staff_member_required(login_url=LOGIN_URL)
def staff_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html")