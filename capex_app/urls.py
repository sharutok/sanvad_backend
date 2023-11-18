from django.urls import path, include
from capex_app.views import (
    read_data_excel,
    get_all_budget_data,
    get_by_capex_id,
    get_by_budget_id,
    create_new_capex,
    get_all_capex_data,
    update_capex,
)

urlpatterns = [
    path("read-data-excel/", read_data_excel, name="read-data-excel"),
    path("get-all-budget-data/", get_all_budget_data, name="get-all-budget-data"),
    path("get-all-capex-data/", get_all_capex_data, name="get-all-capex-data"),
    path("data-budget/<uuid:id>/", get_by_budget_id, name="get-by-budget-id"),
    path("data-capex/<uuid:id>/", get_by_capex_id, name="get-by-capex-id"),
    path("create/", create_new_capex, name="create"),
    path("update/only/", update_capex, name="update-capex"),
]
