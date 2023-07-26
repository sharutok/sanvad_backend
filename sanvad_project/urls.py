from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user-manage/", include("sanvad_app.urls")),
    path("yammer-feeds/", include("yammer_app.urls")),
    path("capex/", include("capex_app.urls")),
]
