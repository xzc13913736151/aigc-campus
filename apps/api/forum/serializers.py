from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from accounts.serializers import UserSerializer
from common.uploads import validate_uploaded_image
from .categories import FORUM_CATEGORIES
from .models import ForumComment, ForumCommentLike, ForumPost, ForumPostImage


class ForumCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = ForumComment
        fields = ("id", "author", "parent", "body", "like_count", "is_liked", "replies", "created_at")
        read_only_fields = ("id", "author", "replies", "created_at")

    @extend_schema_field(serializers.ListField)
    def get_replies(self, obj):
        replies = obj.replies.select_related("author").all()
        return ForumCommentSerializer(replies, many=True, context=self.context).data

    @extend_schema_field(serializers.IntegerField)
    def get_like_count(self, obj):
        return obj.likes.count()

    @extend_schema_field(serializers.BooleanField)
    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def validate_parent(self, value):
        post = self.context.get("post")
        if value and post and value.post_id != post.id:
            raise serializers.ValidationError("Parent comment must belong to the same post.")
        return value


class ForumPostSerializer(serializers.ModelSerializer):
    category = serializers.ChoiceField(choices=FORUM_CATEGORIES)
    author = UserSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    image_urls = serializers.SerializerMethodField()

    class Meta:
        model = ForumPost
        fields = (
            "id",
            "author",
            "title",
            "summary",
            "body",
            "category",
            "tags",
            "is_deleted",
            "is_liked",
            "like_count",
            "comment_count",
            "comments",
            "image_urls",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "author",
            "summary",
            "is_deleted",
            "is_liked",
            "like_count",
            "comment_count",
            "comments",
            "image_urls",
            "created_at",
            "updated_at",
        )

    @extend_schema_field(serializers.CharField)
    def get_summary(self, obj):
        body = obj.body.strip()
        return body[:120] + ("…" if len(body) > 120 else "")

    @extend_schema_field(serializers.IntegerField)
    def get_like_count(self, obj):
        return obj.likes.count()

    @extend_schema_field(serializers.IntegerField)
    def get_comment_count(self, obj):
        return obj.comments.count()

    @extend_schema_field(serializers.BooleanField)
    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    @extend_schema_field(ForumCommentSerializer(many=True))
    def get_comments(self, obj):
        comments = obj.comments.filter(parent__isnull=True).select_related("author").prefetch_related("replies__author")
        return ForumCommentSerializer(comments, many=True, context=self.context).data

    @extend_schema_field(serializers.ListField)
    def get_image_urls(self, obj):
        request = self.context.get("request")
        urls = []
        for image in obj.images.all():
            if request:
                urls.append(request.build_absolute_uri(image.image.url))
            else:
                urls.append(image.image.url)
        return urls


class ForumPostImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ForumPostImage
        fields = ("id", "image", "image_url", "created_at")
        read_only_fields = ("id", "image_url", "created_at")
        extra_kwargs = {
            "image": {"write_only": True},
        }

    @extend_schema_field(serializers.CharField)
    def get_image_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

    def validate_image(self, value):
        return validate_uploaded_image(value, label="帖子图片")
