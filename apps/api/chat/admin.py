from django.contrib import admin

from .models import ChatMessage, ChatThread


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ("user_a", "user_b", "source_type", "created_at", "updated_at")
    search_fields = ("user_a__email", "user_b__email", "source_type", "source_id")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("thread", "sender", "is_read", "created_at")
    search_fields = ("sender__email", "body")
    list_filter = ("is_read", "created_at")
