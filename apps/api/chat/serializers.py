from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from accounts.serializers import UserSerializer

from .models import ChatMessage, ChatThread


User = get_user_model()


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ("id", "sender", "body", "image_url", "is_read", "read_at", "is_withdrawn", "withdrawn_at", "created_at", "updated_at")
        read_only_fields = ("id", "sender", "image_url", "is_read", "read_at", "is_withdrawn", "withdrawn_at", "created_at", "updated_at")

    def get_image_url(self, obj):
        if not obj.image:
            return ""
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class ChatThreadSerializer(serializers.ModelSerializer):
    counterpart = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = ("id", "counterpart", "source_type", "source_id", "last_message", "unread_count", "created_at", "updated_at")
        read_only_fields = fields

    @extend_schema_field(UserSerializer)
    def get_counterpart(self, obj):
        request = self.context.get("request")
        if request is None:
            return None
        counterpart = obj.user_b if obj.user_a_id == request.user.id else obj.user_a
        return UserSerializer(counterpart).data

    @extend_schema_field(ChatMessageSerializer)
    def get_last_message(self, obj):
        message = obj.messages.order_by("-created_at").select_related("sender").first()
        if not message:
            return None
        return ChatMessageSerializer(message, context=self.context).data

    @extend_schema_field(serializers.IntegerField)
    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request is None:
            return 0
        return obj.messages.exclude(sender=request.user).filter(is_read=False).count()


class ChatThreadCreateSerializer(serializers.Serializer):
    target_user_id = serializers.UUIDField()
    source_type = serializers.CharField(required=False, allow_blank=True, max_length=30)
    source_id = serializers.CharField(required=False, allow_blank=True, max_length=64)

    def validate_target_user_id(self, value):
        request = self.context["request"]
        if value == request.user.id:
            raise serializers.ValidationError("You cannot start a chat with yourself.")
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Target user does not exist.")
        return value


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("body",)

    def validate_body(self, value):
        value = value.strip()
        if len(value) < 1:
            raise serializers.ValidationError("Message body is required.")
        return value


class ChatImageMessageCreateSerializer(serializers.Serializer):
    image = serializers.ImageField()


class ChatMarkReadSerializer(serializers.Serializer):
    mark_read = serializers.BooleanField()

    def validate_mark_read(self, value):
        if value is not True:
            raise serializers.ValidationError("Messages can only be marked as read.")
        return value

    def save(self, **kwargs):
        queryset = self.context["queryset"]
        queryset.update(is_read=True, read_at=timezone.now())
        return {"detail": "Messages marked as read."}


class ChatMessageWithdrawSerializer(serializers.Serializer):
    withdraw = serializers.BooleanField()

    def validate_withdraw(self, value):
        if value is not True:
            raise serializers.ValidationError("Message can only be withdrawn.")
        return value
