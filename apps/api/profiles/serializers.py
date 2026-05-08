from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    nickname = serializers.CharField(source="user.nickname", allow_blank=True, required=False, max_length=60)

    class Meta:
        model = Profile
        fields = (
            "id",
            "user",
            "nickname",
            "avatar_url",
            "headline",
            "bio",
            "gender",
            "major",
            "grade",
            "interests",
            "updated_at",
        )
        read_only_fields = ("id", "user", "updated_at")

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        nickname = user_data.get("nickname")
        if nickname is not None:
            instance.user.nickname = nickname.strip()
            instance.user.save(update_fields=["nickname", "updated_at"])
        return super().update(instance, validated_data)
