from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models import UUIDTimeStampedModel


class TeamPost(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        FILLED = "filled", "Filled"
        CLOSED = "closed", "Closed"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_posts")
    title = models.CharField(max_length=120)
    summary = models.CharField(max_length=200)
    details = models.TextField()
    target_size = models.PositiveIntegerField(default=3)
    current_size = models.PositiveIntegerField(default=1)
    required_skills = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    is_highlighted = models.BooleanField(default=False)
    bump_score = models.IntegerField(default=0)
    bumped_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-is_highlighted", "-bump_score", "-bumped_at", "-created_at"]

    def __str__(self) -> str:
        return self.title


class TeamApplication(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    post = models.ForeignKey(TeamPost, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_applications")
    message = models.CharField(max_length=240, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["post", "applicant"], name="unique_team_application"),
        ]

    def __str__(self) -> str:
        return f"{self.applicant} -> {self.post}"
