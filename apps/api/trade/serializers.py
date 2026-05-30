from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import TradeFavorite, TradeMatch, TradePost


class TradePostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = TradePost
        fields = (
            "id",
            "author",
            "post_type",
            "title",
            "description",
            "price",
            "is_negotiable",
            "condition",
            "tags",
            "image_urls",
            "status",
            "view_count",
            "is_highlighted",
            "bump_score",
            "is_favorited",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "author",
            "view_count",
            "is_highlighted",
            "bump_score",
            "created_at",
            "updated_at",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return TradeFavorite.objects.filter(user=request.user, post=obj).exists()


class TradePostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradePost
        fields = (
            "post_type",
            "title",
            "description",
            "price",
            "is_negotiable",
            "condition",
            "tags",
            "image_urls",
        )

    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value


class TradePostStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradePost
        fields = ("status",)

    def validate_status(self, value):
        valid_statuses = {choice[0] for choice in TradePost.Status.choices}
        if value not in valid_statuses:
            raise serializers.ValidationError("交易状态不正确。")
        return value


class TradeFavoriteSerializer(serializers.ModelSerializer):
    post = TradePostSerializer(read_only=True)

    class Meta:
        model = TradeFavorite
        fields = ("id", "post", "created_at")


class TradeMatchSerializer(serializers.ModelSerializer):
    counterparty = serializers.SerializerMethodField()

    class Meta:
        model = TradeMatch
        fields = ("id", "counterparty", "match_type", "related_post", "created_at")

    def get_counterparty(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        user = request.user
        if obj.user_a == user:
            return UserSerializer(obj.user_b).data
        return UserSerializer(obj.user_a).data
