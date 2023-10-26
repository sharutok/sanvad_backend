from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user-manage/", include("sanvad_app.urls")),
    path("yammer-feeds/", include("yammer_app.urls")),
    path("capex/", include("capex_app.urls")),
    path("conf-book/", include("conference_app.urls")),
    path("visitor-manage/", include("visitors_app.urls")),
    path("tkt-sys/", include("ticket_app.urls")),
    path("utils/", include("utils_app.urls")),
    path("wf/", include("workflow_app.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
