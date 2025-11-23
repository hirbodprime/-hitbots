from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("tetris/", include("tetris.urls", namespace="tetris")),
]
urlpatterns += [
    re_path(
        r"^tetris/music/(?P<path>.*)$",
        serve,
        {
            "document_root": os.path.join(settings.BASE_DIR, "tetris", "music"),
        },
    ),
]