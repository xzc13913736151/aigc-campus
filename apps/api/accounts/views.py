from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer

from .serializers import PairUpTokenObtainPairSerializer, RegisterSerializer, UserSerializer


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class PairUpTokenObtainPairView(TokenObtainPairView):
    serializer_class = PairUpTokenObtainPairSerializer


class PairUpTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class CurrentUserAPIView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


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
