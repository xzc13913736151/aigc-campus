from __future__ import annotations

from datetime import timedelta
import secrets

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from common.models import UUIDTimeStampedModel


def generate_claw_id() -> str:
    return f"CC{secrets.token_hex(3).upper()}"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("The email field must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.USER)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, UUIDTimeStampedModel):
    class Role(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    claw_id = models.CharField(max_length=12, unique=True, blank=True)
    wechat_openid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=120, blank=True)
    nickname = models.CharField(max_length=60, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    is_email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        if not self.claw_id:
            while True:
                candidate = generate_claw_id()
                if not User.objects.filter(claw_id=candidate).exists():
                    self.claw_id = candidate
                    break
        super().save(*args, **kwargs)


class EmailVerificationCode(UUIDTimeStampedModel):
    class Purpose(models.TextChoices):
        REGISTER = "register", "Register"

    email = models.EmailField()
    purpose = models.CharField(max_length=20, choices=Purpose.choices, default=Purpose.REGISTER)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "purpose", "-created_at"]),
        ]

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    def set_code(self, raw_code: str) -> None:
        self.code_hash = make_password(raw_code)

    def check_code(self, raw_code: str) -> bool:
        return check_password(raw_code, self.code_hash)

    @classmethod
    def issue(cls, email: str, purpose: str = Purpose.REGISTER) -> tuple["EmailVerificationCode", str]:
        raw_code = f"{secrets.randbelow(1_000_000):06d}"
        instance = cls(
            email=email,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(seconds=settings.EMAIL_VERIFICATION_CODE_TTL_SECONDS),
        )
        instance.set_code(raw_code)
        instance.save()
        return instance, raw_code

    def mark_used(self) -> None:
        self.used_at = timezone.now()
        self.save(update_fields=["used_at", "updated_at"])
