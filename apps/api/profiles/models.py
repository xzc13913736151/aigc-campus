from django.conf import settings
from django.db import models

from common.models import UUIDTimeStampedModel


class Profile(UUIDTimeStampedModel):
    class Gender(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar_url = models.URLField(blank=True)
    headline = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, default=Gender.UNKNOWN)
    major = models.CharField(max_length=120, blank=True)
    grade = models.CharField(max_length=40, blank=True)
    interests = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.user.email} profile"
