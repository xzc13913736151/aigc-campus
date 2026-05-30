from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import AssistantActionProposal, AssistantMessage, AssistantSession


class AssistantMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantMessage
        fields = ("id", "role", "body", "created_at", "updated_at")
        read_only_fields = fields


class AssistantSessionSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = AssistantSession
        fields = (
            "id",
            "title",
            "page_type",
            "context_path",
            "context_target_type",
            "context_target_id",
            "state",
            "last_message",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    @extend_schema_field(AssistantMessageSerializer)
    def get_last_message(self, obj):
        message = obj.messages.order_by("-created_at").first()
        if not message:
            return None
        return AssistantMessageSerializer(message).data


class AssistantSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantSession
        fields = ("title", "page_type", "context_path", "context_target_type", "context_target_id", "state")


class AssistantMessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField()

    def validate_body(self, value: str) -> str:
        value = value.strip()
        if len(value) < 1:
            raise serializers.ValidationError("Message body is required.")
        return value


class AssistantActionProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantActionProposal
        fields = (
            "id",
            "kind",
            "title",
            "target_page",
            "preview",
            "payload",
            "fill_payload",
            "status",
            "expires_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AssistantActionExecuteResponseSerializer(serializers.Serializer):
    action = AssistantActionProposalSerializer()
    result = serializers.DictField()
