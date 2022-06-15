from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, register_converter

from letsdance.core.views import BoardView, IndexView


class KeyConverter:
    regex = "[0-9a-f]{64}"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(KeyConverter, "key")


urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("<key:key>", BoardView.as_view(), name="board"),
    path("admin/", admin.site.urls),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    *staticfiles_urlpatterns(),
]
