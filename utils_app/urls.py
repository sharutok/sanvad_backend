from django.urls import path, include

# from sanvad_app.views import (
#     all_data,
#     data_by_id,
#     create,
#     login_verify_user,
#     birthday_list,
#     user_permission_dynamic_values,
# )
from utils_app.views import download_excel, weather_temp, serve_files

urlpatterns = [
    path("download/excel/", download_excel, name="download-excel"),
    path("get/weather/temp/", weather_temp, name="weather-temp"),
    path("serve/file/", serve_files, name="serve-files"),
]
