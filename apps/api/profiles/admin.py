from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "gender", "major", "grade", "updated_at")
    search_fields = ("user__email", "headline", "major", "grade")
