from django.conf import settings
from django.db import models

from common.models import UUIDTimeStampedModel


class ChatThread(UUIDTimeStampedModel):
    user_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_threads_as_a")
    user_b = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_threads_as_b")
    source_type = models.CharField(max_length=30, blank=True)
    source_id = models.CharField(max_length=64, blank=True)
    hidden_for_user_a = models.BooleanField(default=False)
    hidden_for_user_b = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["user_a", "user_b"], name="unique_chat_thread_pair"),
        ]

    def __str__(self) -> str:
        return f"{self.user_a_id} <-> {self.user_b_id}"


class ChatMessage(UUIDTimeStampedModel):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_chat_messages")
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_withdrawn = models.BooleanField(default=False)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.sender_id} -> {self.thread_id}"
