from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "type",
            "title",
            "body",
            "target_type",
            "target_id",
            "extra",
            "is_read",
            "read_at",
            "actor",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class NotificationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("is_read",)

    def validate_is_read(self, value):
        if value is not True:
            raise serializers.ValidationError("Notifications can only be marked as read.")
        return value

    def update(self, instance, validated_data):
        instance.is_read = True
        instance.read_at = timezone.now()
        instance.save(update_fields=["is_read", "read_at", "updated_at"])
        return instance
