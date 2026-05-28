from django.conf import settings
from django.db import models

from common.models import UUIDTimeStampedModel


class TradePost(UUIDTimeStampedModel):
    class PostType(models.TextChoices):
        SELL = "sell", "Sell"
        BUY = "buy", "Buy"
        EXCHANGE = "exchange", "Exchange"
        SERVICE = "service", "Service"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESERVED = "reserved", "Reserved"
        COMPLETED = "completed", "Completed"
        CLOSED = "closed", "Closed"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trade_posts")
    post_type = models.CharField(max_length=20, choices=PostType.choices, default=PostType.SELL)
    title = models.CharField(max_length=120)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_negotiable = models.BooleanField(default=True)
    condition = models.CharField(max_length=40, blank=True)
    tags = models.JSONField(default=list, blank=True)
    image_urls = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    view_count = models.PositiveIntegerField(default=0)
    is_highlighted = models.BooleanField(default=False)
    bump_score = models.IntegerField(default=0)

    class Meta:
        ordering = ["-is_highlighted", "-bump_score", "-created_at"]

    def __str__(self) -> str:
        return f"{self.get_post_type_display()}: {self.title}"


class TradeFavorite(UUIDTimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trade_favorites")
    post = models.ForeignKey(TradePost, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_trade_favorite"),
        ]


class TradeMatch(UUIDTimeStampedModel):
    class MatchType(models.TextChoices):
        FAVORITE = "favorite", "Favorite"
        CHAT = "chat", "Chat"
        RESERVATION = "reservation", "Reservation"

    user_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trade_matches_as_a")
    user_b = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trade_matches_as_b")
    match_type = models.CharField(max_length=20, choices=MatchType.choices, default=MatchType.FAVORITE)
    related_post = models.ForeignKey(TradePost, on_delete=models.SET_NULL, null=True, blank=True, related_name="matches")

    class Meta:
        ordering = ["-created_at"]