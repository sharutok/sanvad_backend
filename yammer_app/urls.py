from django.urls import path, include
from yammer_app.views import (
    get_api,
    get_weather_data,
    getFileListFromGDrive,
    get_yammer_data_drop_to_redis,
    get_birthday_name,
)

urlpatterns = [
    path("posts/", get_api, name="get-api"),
    path("all-files/", getFileListFromGDrive, name="getFileListFromGDrive"),
    path("run/birthday/get/", get_birthday_name, name="get-birthday-name"),
    path("run/weather/get/", get_weather_data, name="get-weather-data"),
    path(
        "run/yammer/get/",
        get_yammer_data_drop_to_redis,
        name="get-yammer-data-drop-to-redis",
    ),
]
