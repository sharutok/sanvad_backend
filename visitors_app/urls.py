from django.urls import path, include

from visitors_app.views import all_data, create, data_by_id

urlpatterns = [
    path("all/", all_data, name="all-data"),
    path("<uuid:id>", data_by_id, name="data-by-id"),
    path("create/", create, name="create"),
]
