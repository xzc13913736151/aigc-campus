from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import TeamApplication, TeamPost


class TeamPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = TeamPost
        fields = (
            "id",
            "author",
            "title",
            "summary",
            "details",
            "target_size",
            "current_size",
            "required_skills",
            "tags",
            "status",
            "is_highlighted",
            "bump_score",
            "bumped_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "author", "current_size", "is_highlighted", "bump_score", "bumped_at", "created_at", "updated_at")


class TeamApplicationSerializer(serializers.ModelSerializer):
    applicant = UserSerializer(read_only=True)
    post = TeamPostSerializer(read_only=True)

    class Meta:
        model = TeamApplication
        fields = ("id", "post", "applicant", "message", "status", "created_at", "updated_at")
        read_only_fields = ("id", "post", "applicant", "status", "created_at", "updated_at")


class TeamApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamApplication
        fields = ("id", "message")
        read_only_fields = ("id",)


class TeamApplicationReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamApplication
        fields = ("status",)

    def validate_status(self, value):
        if value not in {TeamApplication.Status.ACCEPTED, TeamApplication.Status.REJECTED}:
            raise serializers.ValidationError("Status must be accepted or rejected.")
        return value
