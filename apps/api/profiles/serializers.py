from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ("id", "user", "avatar_url", "headline", "bio", "gender", "major", "grade", "interests", "updated_at")
        read_only_fields = ("id", "user", "updated_at")
