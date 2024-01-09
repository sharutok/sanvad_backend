from django.urls import path, include
from yammer_app.views import get_api, getFileListFromGDrive

urlpatterns = [
    path("posts/", get_api, name="get-api"),
    path("all-files/", getFileListFromGDrive, name="getFileListFromGDrive"),
]
