from django.urls import path, include
from policies_app.views import get_all_data, create_policy

urlpatterns = [
    path("get-all-data/", get_all_data, name="get-all-data"),
    path("post/", create_policy, name="create-policy"),
]
