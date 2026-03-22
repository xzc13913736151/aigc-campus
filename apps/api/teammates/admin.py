from django.contrib import admin

from .models import TeamApplication, TeamPost


@admin.register(TeamPost)
class TeamPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "target_size", "current_size", "is_highlighted", "created_at")
    list_filter = ("status", "is_highlighted")
    search_fields = ("title", "summary", "details", "author__email")


@admin.register(TeamApplication)
class TeamApplicationAdmin(admin.ModelAdmin):
    list_display = ("post", "applicant", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("post__title", "applicant__email")
