from django.urls import path, include

from visitors_app.views import (
    all_data,
    create,
    data_by_id,
    save_image,
    get_image,
    punch,
)

urlpatterns = [
    path("all/", all_data, name="all-data"),
    path("<uuid:id>", data_by_id, name="data-by-id"),
    path("create/", create, name="create"),
    path("save/img/", save_image, name="save-image"),
    path("get/img/", get_image, name="get-image"),
    path("punch/", punch, name="punch"),
]
