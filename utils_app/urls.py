from django.urls import path, include

from utils_app.views import download_excel, weather_temp, serve_files, announcement

urlpatterns = [
    path("download/excel/", download_excel, name="download-excel"),
    path("get/weather/temp/", weather_temp, name="weather-temp"),
    path("serve/file/", serve_files, name="serve-files"),
    path("add/announsment/", announcement, name="announcement"),
]
