from django.conf import settings
from django.db import models

from common.models import UUIDTimeStampedModel


class Report(UUIDTimeStampedModel):
    class TargetType(models.TextChoices):
        USER = "user", "User"
        DATING_PROFILE = "dating_profile", "Dating profile"
        TEAM_POST = "team_post", "Team post"
        FORUM_POST = "forum_post", "Forum post"
        COMMENT = "comment", "Comment"
        TRADE_POST = "trade_post", "Trade post"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWING = "reviewing", "Reviewing"
        RESOLVED = "resolved", "Resolved"
        REJECTED = "rejected", "Rejected"

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    target_type = models.CharField(max_length=30, choices=TargetType.choices)
    target_id = models.UUIDField()
    reason = models.CharField(max_length=160)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    class Meta:
        ordering = ["-created_at"]


class Block(UUIDTimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks_created")
    blocked_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocked_by_users")
    reason = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "blocked_user"], name="unique_block_relation"),
        ]


class ModerationActionLog(UUIDTimeStampedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="moderation_action_logs")
    report = models.ForeignKey(Report, on_delete=models.SET_NULL, null=True, blank=True, related_name="action_logs")
    action = models.CharField(max_length=60)
    target_type = models.CharField(max_length=30, blank=True)
    target_id = models.UUIDField(null=True, blank=True)
    note = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
