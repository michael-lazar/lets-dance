from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from letsdance.core.models import Board, Peer


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ["id", "key", "last_modified"]
    search_fields = ["key"]
    readonly_fields = ["url"]
    fields = ["key", "content", "signature", "last_modified", "url"]

    @admin.display(description="URL")
    def url(self, obj: Board) -> str:
        url = reverse("board", args=[obj.key])
        return format_html("<a href='{}'>{}</a>", url, url)


@admin.register(Peer)
class PeerAdmin(admin.ModelAdmin):
    list_display = ["id", "url"]
    search_fields = ["url"]
