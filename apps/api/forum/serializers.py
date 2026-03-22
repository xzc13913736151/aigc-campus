from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from accounts.serializers import UserSerializer
from .models import ForumComment, ForumPost


class ForumCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = ForumComment
        fields = ("id", "author", "parent", "body", "created_at")
        read_only_fields = ("id", "author", "created_at")


class ForumPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = ForumCommentSerializer(many=True, read_only=True)
    like_count = serializers.SerializerMethodField()

    class Meta:
        model = ForumPost
        fields = ("id", "author", "title", "body", "category", "tags", "is_deleted", "like_count", "comments", "created_at", "updated_at")
        read_only_fields = ("id", "author", "is_deleted", "like_count", "comments", "created_at", "updated_at")

    @extend_schema_field(serializers.IntegerField)
    def get_like_count(self, obj):
        return obj.likes.count()
