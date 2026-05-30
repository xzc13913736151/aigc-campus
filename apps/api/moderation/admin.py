from django.contrib import admin

from .models import Block, ModerationActionLog, Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("target_type", "target_id", "reporter", "status", "created_at")
    list_filter = ("target_type", "status")
    search_fields = ("reason", "reporter__email")


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("user", "blocked_user", "reason", "created_at")
    search_fields = ("user__email", "blocked_user__email", "reason")


@admin.register(ModerationActionLog)
class ModerationActionLogAdmin(admin.ModelAdmin):
    list_display = ("action", "target_type", "target_id", "actor", "created_at")
    list_filter = ("action", "target_type")
    search_fields = ("note", "actor__email")
