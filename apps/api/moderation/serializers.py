from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from accounts.serializers import UserSerializer
from forum.models import ForumComment, ForumPost

from .models import Block, Report


class ReportSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)

    class Meta:
        model = Report
        fields = ("id", "reporter", "target_type", "target_id", "reason", "details", "status", "created_at")
        read_only_fields = ("id", "reporter", "status", "created_at")


class AdminReportSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)
    target_snapshot = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = (
            "id",
            "reporter",
            "target_type",
            "target_id",
            "target_snapshot",
            "reason",
            "details",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    @extend_schema_field(serializers.DictField)
    def get_target_snapshot(self, obj):
        if obj.target_type == Report.TargetType.FORUM_POST:
            post = ForumPost.objects.filter(id=obj.target_id).select_related("author").first()
            if not post:
                return {"exists": False, "label": "Forum post not found"}
            return {
                "exists": True,
                "label": post.title,
                "author_email": post.author.email,
                "is_deleted": post.is_deleted,
            }
        if obj.target_type == Report.TargetType.COMMENT:
            comment = ForumComment.objects.filter(id=obj.target_id).select_related("author", "post").first()
            if not comment:
                return {"exists": False, "label": "Comment not found"}
            preview = comment.body.strip()
            return {
                "exists": True,
                "label": preview[:40] + ("..." if len(preview) > 40 else ""),
                "author_email": comment.author.email,
                "post_id": str(comment.post_id),
            }
        return {"exists": True, "label": obj.target_type}


class AdminReportReviewSerializer(serializers.ModelSerializer):
    action = serializers.ChoiceField(
        choices=["none", "delete_forum_post", "delete_forum_comment"],
        required=False,
        default="none",
        write_only=True,
    )

    class Meta:
        model = Report
        fields = ("status", "action")

    def validate(self, attrs):
        action = attrs.get("action", "none")
        instance: Report = self.instance
        if action == "delete_forum_post" and instance.target_type != Report.TargetType.FORUM_POST:
            raise serializers.ValidationError({"action": "Only forum post reports support delete_forum_post."})
        if action == "delete_forum_comment" and instance.target_type != Report.TargetType.COMMENT:
            raise serializers.ValidationError({"action": "Only comment reports support delete_forum_comment."})
        return attrs

    def save(self, **kwargs):
        instance: Report = self.instance
        action = self.validated_data.get("action", "none")
        status = self.validated_data["status"]

        if action == "delete_forum_post":
            post = ForumPost.objects.filter(id=instance.target_id).first()
            if post is None:
                raise serializers.ValidationError({"action": "Target forum post does not exist."})
            if not post.is_deleted:
                post.is_deleted = True
                post.save(update_fields=["is_deleted", "updated_at"])
        elif action == "delete_forum_comment":
            comment = ForumComment.objects.filter(id=instance.target_id).first()
            if comment is None:
                raise serializers.ValidationError({"action": "Target forum comment does not exist."})
            comment.delete()

        instance.status = status
        instance.save(update_fields=["status", "updated_at"])
        return instance


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
