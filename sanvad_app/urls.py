from django.urls import path, include
from sanvad_app.views import all_data, data_by_id, create, get_api

urlpatterns = [
    path("all/", all_data, name="all-data"),
    path("<uuid:id>", data_by_id, name="data-by-id"),
    path("create/", create, name="create"),
    path("yammer-api-feeds/", get_api, name="get-api"),
]
