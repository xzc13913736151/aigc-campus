from django.conf import settings
from django.db import models

from common.models import UUIDTimeStampedModel


class AssistantSession(UUIDTimeStampedModel):
    class PageType(models.TextChoices):
        FORUM = "forum", "Forum"
        PUBLISH = "publish", "Publish"
        MESSAGES = "messages", "Messages"
        ME = "me", "Me"
        GENERAL = "general", "General"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assistant_sessions")
    title = models.CharField(max_length=120, blank=True)
    page_type = models.CharField(max_length=20, choices=PageType.choices, default=PageType.GENERAL)
    context_path = models.CharField(max_length=120, blank=True)
    context_target_type = models.CharField(max_length=40, blank=True)
    context_target_id = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.user_id} - {self.page_type}"


class AssistantMessage(UUIDTimeStampedModel):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    session = models.ForeignKey(AssistantSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=Role.choices)
    body = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.session_id} - {self.role}"
