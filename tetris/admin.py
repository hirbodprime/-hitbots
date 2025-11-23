from django.contrib import admin
from .models import TetrisScore

@admin.register(TetrisScore)
class TetrisScoreAdmin(admin.ModelAdmin):
    list_display = ("user_id", "username", "chat_id", "score", "created_at")
    list_filter = ("chat_id",)
    search_fields = ("username", "user_id")
