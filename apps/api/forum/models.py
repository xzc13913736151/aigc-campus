from django.conf import settings
from django.db import models

from common.models import UUIDTimeStampedModel


class ForumPost(UUIDTimeStampedModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_posts")
    title = models.CharField(max_length=160)
    body = models.TextField()
    category = models.CharField(max_length=80, blank=True)
    tags = models.JSONField(default=list, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class ForumPostImage(UUIDTimeStampedModel):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="forum/posts/%Y/%m/%d/")

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Image for {self.post_id}"


class ForumComment(UUIDTimeStampedModel):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    body = models.TextField()

    class Meta:
        ordering = ["created_at"]


class ForumPostLike(UUIDTimeStampedModel):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_post_likes")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="unique_forum_post_like"),
        ]
