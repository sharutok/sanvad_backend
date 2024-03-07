from django.urls import path, include
from sanvad_app.views import (
    all_data,
    data_by_id,
    create,
    login_verify_user,
    birthday_list,
    user_permission_dynamic_values,
    reset_password,validate_remember_me,
    get_list_of_managers_based_on_department,
)

urlpatterns = [
    path("all/", all_data, name="all-data"),
    path("<uuid:id>/", data_by_id, name="data-by-id"),
    path("create/", create, name="create"),
    path("login/check/", login_verify_user, name="login-verify-user"),
    path("birthday/list/", birthday_list, name="birthday-list"),
    path(
        "user/permission/list/", user_permission_dynamic_values, name="user-permission"
    ),
    path("reset/password", reset_password, name="reset-password"),
    path(
        "list/manager/",
        get_list_of_managers_based_on_department,
        name="get-list-of-managers-based-on-department",
    ),
    path("validate/token/",validate_remember_me,name="validate-remember-me")
]
