from django.contrib import admin

from .models import DatingMatch, DatingPreference, DatingProfile, DatingSignal


@admin.register(DatingProfile)
class DatingProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "nickname", "gender", "height_cm", "weight_kg", "age", "is_visible", "updated_at")
    search_fields = ("user__email", "nickname")


@admin.register(DatingPreference)
class DatingPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "min_height_cm", "max_height_cm", "min_weight_kg", "max_weight_kg", "min_age", "max_age", "updated_at")
    search_fields = ("user__email",)


@admin.register(DatingSignal)
class DatingSignalAdmin(admin.ModelAdmin):
    list_display = ("actor", "target", "signal", "created_at")
    list_filter = ("signal",)
    search_fields = ("actor__email", "target__email")


@admin.register(DatingMatch)
class DatingMatchAdmin(admin.ModelAdmin):
    list_display = ("user_a", "user_b", "created_at")
    search_fields = ("user_a__email", "user_b__email")
