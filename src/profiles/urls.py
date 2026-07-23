from django.urls import path, include
from .views import profile_detail_view, profile_list_view


urlpatterns = [
    path('', profile_list_view),
    path('<username>/',  profile_detail_view),
]
