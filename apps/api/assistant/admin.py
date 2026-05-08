from django.contrib import admin

from .models import AssistantMessage, AssistantSession


@admin.register(AssistantSession)
class AssistantSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "page_type", "title", "updated_at")
    list_filter = ("page_type",)
    search_fields = ("user__email", "title", "context_path")


@admin.register(AssistantMessage)
class AssistantMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("session__user__email", "body")
