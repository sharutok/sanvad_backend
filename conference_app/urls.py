from django.urls import path, include

from conference_app.views import (
    all_data,
    create,
    data_by_id,
    get_data_by_cof_room_and_date,
    conference_rooms_dynamic_values,
)

urlpatterns = [
    path("all/", all_data, name="all-data"),
    path("<uuid:id>", data_by_id, name="data-by-id"),
    path("create/", create, name="create"),
    path(
        "conference-rooms/",
        conference_rooms_dynamic_values,
        name="conference-rooms-dynamic-values",
    ),
    path(
        "by/date/conf-room/",
        get_data_by_cof_room_and_date,
        name="get-data-by-cof-room-and-date",
    ),
]
