from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("type", "recipient", "actor", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at")
    search_fields = ("title", "body", "recipient__email", "actor__email")
    readonly_fields = ("id", "created_at", "updated_at", "read_at")
