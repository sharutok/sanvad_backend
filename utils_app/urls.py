from django.urls import path, include

# from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from utils_app.views import (
    download_excel,
    weather_temp,
    serve_files,
    announcement,
    plant_department_values,
    wish_birthday,
    new_user_creation_mail,
    which_frame,
    delete_data_in_yammer,
)

urlpatterns = [
    path("download/excel/", download_excel, name="download-excel"),
    path("get/weather/temp/", weather_temp, name="weather-temp"),
    path("serve/file/", serve_files, name="serve-files"),
    path("add/announsment/", announcement, name="announcement"),
    path("list/dept-plant/", plant_department_values, name="plant-department-values"),
    path("birthday/wish/", wish_birthday, name="wish-birthday"),
    path(
        "new/user/creation/mail/", new_user_creation_mail, name="new-user-creation-mail"
    ),
    path("which/frame/", which_frame, name="which-frame"),
    path(
        "delete/yammer/old/files", delete_data_in_yammer, name="delete-data-in-yammer"
    ),
]

# urlpatterns += staticfiles_urlpatterns()
