from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers

from moderation.services import get_blocked_user_ids, is_blocked_pair

from .models import DatingMatch, DatingPreference, DatingProfile, DatingSignal
from .serializers import (
    DatingCandidateSerializer,
    DatingMatchSerializer,
    DatingPreferenceSerializer,
    DatingProfileSerializer,
    DatingSignalSerializer,
)


User = get_user_model()


def canonical_match_users(first, second):
    return (first, second) if str(first.id) < str(second.id) else (second, first)


def calculate_match_score(profile: DatingProfile, preference: DatingPreference | None) -> int:
    if preference is None:
        return 50

    score = 0
    if not preference.preferred_genders or profile.gender in preference.preferred_genders:
        score += 25

    if profile.height_cm is not None:
        min_height_ok = preference.min_height_cm is None or profile.height_cm >= preference.min_height_cm
        max_height_ok = preference.max_height_cm is None or profile.height_cm <= preference.max_height_cm
        if min_height_ok and max_height_ok:
            score += 20

    if not preference.preferred_personality_types or profile.personality_type in preference.preferred_personality_types:
        score += 20

    overlap = len(set(profile.interests) & set(preference.preferred_interests))
    score += min(overlap * 10, 35)

    return min(score, 100)


class DatingProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = DatingProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = DatingProfile.objects.get_or_create(user=self.request.user)
        return profile


class DatingPreferenceAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = DatingPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        preference, _ = DatingPreference.objects.get_or_create(user=self.request.user)
        return preference


class DatingCandidateListAPIView(generics.ListAPIView):
    serializer_class = DatingCandidateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        blocked_user_ids = get_blocked_user_ids(self.request.user)
        return (
            DatingProfile.objects.select_related("user")
            .filter(is_visible=True)
            .exclude(user=self.request.user)
            .exclude(user_id__in=blocked_user_ids)
        )

    def list(self, request, *args, **kwargs):
        queryset = list(self.get_queryset())
        preference = DatingPreference.objects.filter(user=request.user).first()
        payload = []
        for profile in queryset:
            data = DatingCandidateSerializer(profile, context=self.get_serializer_context()).data
            data["match_score"] = calculate_match_score(profile, preference)
            payload.append(data)

        payload.sort(key=lambda item: item["match_score"], reverse=True)
        return Response(payload)


class DatingSignalAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=DatingSignalSerializer,
        responses={
            200: inline_serializer(
                name="DatingSignalResponse",
                fields={
                    "matched": serializers.BooleanField(),
                    "signal": serializers.ChoiceField(choices=DatingSignal.Signal.choices),
                },
            ),
            400: OpenApiResponse(description="The user attempted to signal themselves."),
        },
    )
    def post(self, request):
        serializer = DatingSignalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target = User.objects.get(pk=serializer.validated_data["target_user_id"])
        if target.id == request.user.id:
            return Response({"detail": "You cannot signal yourself."}, status=status.HTTP_400_BAD_REQUEST)
        if is_blocked_pair(request.user, target):
            return Response({"detail": "You cannot interact with a blocked user."}, status=status.HTTP_400_BAD_REQUEST)

        signal_obj, _ = DatingSignal.objects.update_or_create(
            actor=request.user,
            target=target,
            defaults={"signal": serializer.validated_data["signal"]},
        )

        matched = False
        if signal_obj.signal == DatingSignal.Signal.INTERESTED:
            reverse_signal = DatingSignal.objects.filter(
                actor=target,
                target=request.user,
                signal=DatingSignal.Signal.INTERESTED,
            ).exists()
            if reverse_signal:
                user_a, user_b = canonical_match_users(request.user, target)
                DatingMatch.objects.get_or_create(user_a=user_a, user_b=user_b)
                matched = True

        return Response({"matched": matched, "signal": signal_obj.signal}, status=status.HTTP_200_OK)


class DatingMatchListAPIView(generics.ListAPIView):
    serializer_class = DatingMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        blocked_user_ids = get_blocked_user_ids(self.request.user)
        return (
            DatingMatch.objects.select_related("user_a", "user_b")
            .filter(Q(user_a=self.request.user) | Q(user_b=self.request.user))
            .exclude(user_a_id__in=blocked_user_ids)
            .exclude(user_b_id__in=blocked_user_ids)
        )
