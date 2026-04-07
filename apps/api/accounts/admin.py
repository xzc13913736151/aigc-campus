from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import EmailVerificationCode, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-created_at",)
    list_display = ("email", "role", "is_email_verified", "is_staff", "is_active", "created_at")
    list_filter = ("role", "is_email_verified", "is_staff", "is_active")
    search_fields = ("email", "full_name", "nickname")
    readonly_fields = ("id", "created_at", "updated_at", "last_login", "email_verified_at")
    fieldsets = (
        ("Identity", {"fields": ("id", "email", "password")}),
        ("Profile", {"fields": ("full_name", "nickname", "role", "is_email_verified", "email_verified_at")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Audit", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role", "is_staff", "is_superuser"),
            },
        ),
    )


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "purpose", "expires_at", "used_at", "created_at")
    list_filter = ("purpose", "used_at")
    search_fields = ("email",)
    readonly_fields = ("id", "code_hash", "expires_at", "used_at", "created_at", "updated_at")
