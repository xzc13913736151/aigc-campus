from django.conf import settings
from django.db import models

from common.models import UUIDTimeStampedModel


class DatingProfile(UUIDTimeStampedModel):
    class Gender(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dating_profile")
    nickname = models.CharField(max_length=60, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, default=Gender.UNKNOWN)
    height_cm = models.PositiveIntegerField(null=True, blank=True)
    interests = models.JSONField(default=list, blank=True)
    personality_type = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["-updated_at"]


class DatingPreference(UUIDTimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dating_preference")
    preferred_genders = models.JSONField(default=list, blank=True)
    min_height_cm = models.PositiveIntegerField(null=True, blank=True)
    max_height_cm = models.PositiveIntegerField(null=True, blank=True)
    preferred_interests = models.JSONField(default=list, blank=True)
    preferred_personality_types = models.JSONField(default=list, blank=True)


class DatingSignal(UUIDTimeStampedModel):
    class Signal(models.TextChoices):
        INTERESTED = "interested", "Interested"
        NOT_INTERESTED = "not_interested", "Not interested"

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dating_signals_sent")
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dating_signals_received")
    signal = models.CharField(max_length=20, choices=Signal.choices)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["actor", "target"], name="unique_dating_signal"),
        ]


class DatingMatch(UUIDTimeStampedModel):
    user_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dating_matches_as_a")
    user_b = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dating_matches_as_b")

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user_a", "user_b"], name="unique_dating_match"),
        ]
