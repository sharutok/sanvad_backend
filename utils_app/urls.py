from django.urls import path, include

# from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from utils_app.views import (
    download_excel,
    weather_temp,
    serve_files,
    announcement,
    plant_department_values,
)

urlpatterns = [
    path("download/excel/", download_excel, name="download-excel"),
    path("get/weather/temp/", weather_temp, name="weather-temp"),
    path("serve/file/", serve_files, name="serve-files"),
    path("add/announsment/", announcement, name="announcement"),
    path("list/dept-plant/", plant_department_values, name="plant-department-values"),
]

# urlpatterns += staticfiles_urlpatterns()
