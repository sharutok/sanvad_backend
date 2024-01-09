from django.urls import path, include
from ticket_app.views import (
    all_data,
    create,
    ticket_type_dynamic_values,
    req_type_dynamic_values,
    data_by_id,
    get_all_user_list,
    view_all_tickets,
)


urlpatterns = [
    path("all/", all_data, name="all-data"),
    path("<uuid:id>/", data_by_id, name="data-by-id"),
    path("create/", create, name="create"),
    path(
        "tkt_type/",
        ticket_type_dynamic_values,
        name="ticket-type-dynamic-values",
    ),
    path("req_type/", req_type_dynamic_values, name="req-type-dynamic-values"),
    path("get-all-users/", get_all_user_list, name="get-all-user-list"),
    path("view/all/", view_all_tickets, name="view-all-tickets"),
]
