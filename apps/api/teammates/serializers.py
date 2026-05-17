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

    def validate_target_size(self, value):
        if value < 2 or value > 20:
            raise serializers.ValidationError("Target size must be between 2 and 20.")
        return value

    def validate_status(self, value):
        if value not in {TeamPost.Status.OPEN, TeamPost.Status.FILLED, TeamPost.Status.CLOSED}:
            raise serializers.ValidationError("Invalid team post status.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        target_size = attrs.get("target_size", getattr(self.instance, "target_size", 3))
        current_size = getattr(self.instance, "current_size", 1)
        if target_size < current_size:
            raise serializers.ValidationError({"target_size": "Target size cannot be smaller than current team size."})
        return attrs


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

    def validate_message(self, value):
        return value.strip()


class TeamApplicationReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamApplication
        fields = ("status",)

    def validate_status(self, value):
        if value not in {TeamApplication.Status.ACCEPTED, TeamApplication.Status.REJECTED}:
            raise serializers.ValidationError("Status must be accepted or rejected.")
        return value
