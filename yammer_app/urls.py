from django.urls import path, include
from yammer_app.views import get_api

urlpatterns = [
    path("posts/", get_api, name="get-api"),
]
