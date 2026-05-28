from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from accounts.serializers import UserSerializer
from .models import DatingMatch, DatingPreference, DatingProfile, DatingSignal


class DatingProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = DatingProfile
        fields = ("id", "user", "nickname", "gender", "height_cm", "weight_kg", "age", "interests", "personality_type", "bio", "is_visible", "updated_at")
        read_only_fields = ("id", "user", "updated_at")


class DatingPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatingPreference
        fields = (
            "id",
            "preferred_genders",
            "min_height_cm",
            "max_height_cm",
            "min_weight_kg",
            "max_weight_kg",
            "min_age",
            "max_age",
            "preferred_interests",
            "preferred_personality_types",
            "updated_at",
        )
        read_only_fields = ("id", "updated_at")


class DatingSignalSerializer(serializers.ModelSerializer):
    target_user_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = DatingSignal
        fields = ("id", "target_user_id", "signal", "created_at")
        read_only_fields = ("id", "created_at")


class DatingMatchSerializer(serializers.ModelSerializer):
    counterpart = serializers.SerializerMethodField()

    class Meta:
        model = DatingMatch
        fields = ("id", "counterpart", "created_at")

    @extend_schema_field(UserSerializer)
    def get_counterpart(self, obj):
        request = self.context.get("request")
        if request is None:
            return None
        counterpart = obj.user_b if obj.user_a_id == request.user.id else obj.user_a
        return UserSerializer(counterpart).data


class DatingCandidateSerializer(DatingProfileSerializer):
    match_score = serializers.IntegerField(read_only=True)

    class Meta(DatingProfileSerializer.Meta):
        fields = DatingProfileSerializer.Meta.fields + ("match_score",)
        read_only_fields = DatingProfileSerializer.Meta.read_only_fields + ("match_score",)
