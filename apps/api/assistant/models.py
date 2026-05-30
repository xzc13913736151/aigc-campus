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
    state = models.JSONField(default=dict, blank=True)

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


class AssistantActionProposal(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        EXECUTED = "executed", "Executed"
        DISMISSED = "dismissed", "Dismissed"
        EXPIRED = "expired", "Expired"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assistant_action_proposals")
    session = models.ForeignKey(AssistantSession, on_delete=models.CASCADE, related_name="action_proposals")
    message = models.ForeignKey(AssistantMessage, on_delete=models.CASCADE, related_name="action_proposals", null=True, blank=True)
    kind = models.CharField(max_length=80)
    title = models.CharField(max_length=160)
    target_page = models.CharField(max_length=160, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    preview = models.JSONField(default=dict, blank=True)
    fill_payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField()
    executed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user_id} - {self.kind} - {self.status}"
