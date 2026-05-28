from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer

from moderation.services import get_blocked_user_ids

from .serializers import (
    ContactSearchUserSerializer,
    EmailCodeRequestSerializer,
    PairUpTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
    WechatLoginSerializer,
)
from django.contrib.auth import get_user_model
from django.db.models import Q


User = get_user_model()


class EmailCodeRequestAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=EmailCodeRequestSerializer,
        responses={
            202: inline_serializer(
                name="EmailCodeRequestResponse",
                fields={
                    "detail": serializers.CharField(),
                    "email": serializers.EmailField(),
                    "expires_in": serializers.IntegerField(),
                },
            ),
        },
    )
    def post(self, request):
        serializer = EmailCodeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        return Response(payload, status=status.HTTP_202_ACCEPTED)


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class PairUpTokenObtainPairView(TokenObtainPairView):
    serializer_class = PairUpTokenObtainPairSerializer


class WechatLoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=WechatLoginSerializer)
    def post(self, request):
        serializer = WechatLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        return Response(payload, status=status.HTTP_200_OK)


class PairUpTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class CurrentUserAPIView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ContactSearchAPIView(generics.ListAPIView):
    serializer_class = ContactSearchUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()
        if len(query) < 2:
            return User.objects.none()

        blocked_user_ids = get_blocked_user_ids(self.request.user)
        queryset = (
            User.objects.select_related("profile")
            .filter(is_active=True)
            .exclude(id=self.request.user.id)
            .exclude(id__in=blocked_user_ids)
        )
        normalized_query = query.upper()
        return queryset.filter(
            Q(claw_id__iexact=normalized_query)
            | Q(nickname__icontains=query)
            | Q(full_name__icontains=query)
        )[:20]


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            name="LogoutRequest",
            fields={
                "refresh": serializers.CharField(required=False),
            },
        ),
        responses={204: OpenApiResponse(description="Logged out successfully.")},
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)
