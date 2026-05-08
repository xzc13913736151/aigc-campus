from django.conf import settings
from django.db import models

from common.models import UUIDTimeStampedModel


class Notification(UUIDTimeStampedModel):
    class Type(models.TextChoices):
        FORUM_LIKE = "forum_like", "Forum like"
        FORUM_COMMENT = "forum_comment", "Forum comment"
        FORUM_REPLY = "forum_reply", "Forum reply"
        TEAM_APPLICATION_CREATED = "team_application_created", "Team application created"
        TEAM_APPLICATION_ACCEPTED = "team_application_accepted", "Team application accepted"
        TEAM_APPLICATION_REJECTED = "team_application_rejected", "Team application rejected"
        CHAT_MESSAGE = "chat_message", "Chat message"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=40, choices=Type.choices)
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=280)
    target_type = models.CharField(max_length=40, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    extra = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["is_read", "-created_at"]

    def __str__(self) -> str:
        return f"{self.recipient} - {self.type}"
