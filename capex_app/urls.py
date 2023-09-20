from django.urls import path, include
from capex_app.views import read_data_excel, get_all_data, get_by_id, create

urlpatterns = [
    path("read-data-excel/", read_data_excel, name="read-data-excel"),
    path("get-all-data/", get_all_data, name="get-all-data"),
    path("<uuid:id>/", get_by_id, name="get-by-id"),
    path("create/", create, name="create"),
]
