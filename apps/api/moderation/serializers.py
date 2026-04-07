from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from accounts.serializers import UserSerializer
from .models import Block, Report


class ReportSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)

    class Meta:
        model = Report
        fields = ("id", "reporter", "target_type", "target_id", "reason", "details", "status", "created_at")
        read_only_fields = ("id", "reporter", "status", "created_at")


class BlockSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    blocked_user = serializers.UUIDField(write_only=True)
    blocked_user_detail = serializers.SerializerMethodField()

    class Meta:
        model = Block
        fields = ("id", "user", "blocked_user", "blocked_user_detail", "reason", "created_at")
        read_only_fields = ("id", "user", "blocked_user_detail", "created_at")

    @extend_schema_field(UserSerializer)
    def get_blocked_user_detail(self, obj):
        return UserSerializer(obj.blocked_user).data
