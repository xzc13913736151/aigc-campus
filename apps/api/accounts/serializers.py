from __future__ import annotations

from datetime import timedelta
import hashlib
import secrets

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerificationCode


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "claw_id",
            "email",
            "full_name",
            "nickname",
            "role",
            "is_email_verified",
            "email_verified_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "claw_id", "role", "is_email_verified", "email_verified_at", "created_at", "updated_at")


class ContactSearchUserSerializer(serializers.ModelSerializer):
    headline = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "claw_id", "nickname", "full_name", "headline", "avatar_url")
        read_only_fields = fields

    def get_headline(self, obj):
        profile = getattr(obj, "profile", None)
        return getattr(profile, "headline", "") if profile else ""

    def get_avatar_url(self, obj):
        profile = getattr(obj, "profile", None)
        return getattr(profile, "avatar_url", "") if profile else ""


class EmailCodeRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    default_error_messages = {
        "already_registered": "This email is already registered.",
        "cooldown": "Please wait before requesting another code.",
    }

    def validate_email(self, value):
        email = User.objects.normalize_email(value).strip()
        if User.objects.filter(email=email).exists():
            self.fail("already_registered")

        latest_code = (
            EmailVerificationCode.objects.filter(email=email, purpose=EmailVerificationCode.Purpose.REGISTER)
            .order_by("-created_at")
            .first()
        )
        resend_after = timedelta(seconds=settings.EMAIL_VERIFICATION_RESEND_INTERVAL_SECONDS)
        if latest_code and timezone.now() - latest_code.created_at < resend_after:
            self.fail("cooldown")

        return email

    def create(self, validated_data):
        email = validated_data["email"]
        _, raw_code = EmailVerificationCode.issue(email=email)
        ttl_minutes = max(settings.EMAIL_VERIFICATION_CODE_TTL_SECONDS // 60, 1)
        send_mail(
            subject="PairUp verification code",
            message=(
                f"Your PairUp verification code is {raw_code}.\n\n"
                f"It expires in {ttl_minutes} minute(s)."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return {
            "detail": "Verification code sent.",
            "email": email,
            "expires_in": settings.EMAIL_VERIFICATION_CODE_TTL_SECONDS,
        }


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    verification_code = serializers.CharField(write_only=True, min_length=6, max_length=6)

    class Meta:
        model = User
        fields = ("id", "email", "password", "verification_code", "full_name", "nickname")
        read_only_fields = ("id",)

    def validate_email(self, value):
        return User.objects.normalize_email(value).strip()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        email = attrs["email"]
        verification_code = attrs["verification_code"]
        latest_code = (
            EmailVerificationCode.objects.filter(
                email=email,
                purpose=EmailVerificationCode.Purpose.REGISTER,
                used_at__isnull=True,
            )
            .order_by("-created_at")
            .first()
        )
        if not latest_code or latest_code.is_expired or not latest_code.check_code(verification_code):
            raise serializers.ValidationError({"verification_code": "Invalid or expired verification code."})
        attrs["verification_record"] = latest_code
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("verification_code")
        verification_record = validated_data.pop("verification_record")
        with transaction.atomic():
            user = User.objects.create_user(
                password=password,
                is_email_verified=True,
                email_verified_at=timezone.now(),
                **validated_data,
            )
            verification_record.mark_used()
        return user


class PairUpTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class WechatLoginSerializer(serializers.Serializer):
    code = serializers.CharField()

    default_error_messages = {
        "wechat_unconfigured": "WeChat mini program credentials are not configured.",
        "wechat_code_invalid": "WeChat login failed.",
        "wechat_openid_missing": "WeChat login response is missing openid.",
        "wechat_unreachable": "WeChat login service is temporarily unavailable.",
    }

    def validate_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("WeChat login code is required.")
        return value

    def _build_login_payload(self, openid: str, nickname: str):
        with transaction.atomic():
            user = User.objects.filter(wechat_openid=openid).first()
            if user is None:
                digest = hashlib.sha256(openid.encode("utf-8")).hexdigest()[:24]
                email = f"wx_{digest}@wechat.pairup.local"
                user = User.objects.create_user(
                    email=email,
                    password=None,
                    nickname=nickname,
                    full_name="",
                    wechat_openid=openid,
                    is_email_verified=False,
                )

        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }

    def create(self, validated_data):
        if not settings.WECHAT_MINIAPP_APPID or not settings.WECHAT_MINIAPP_SECRET:
            self.fail("wechat_unconfigured")

        try:
            response = requests.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params={
                    "appid": settings.WECHAT_MINIAPP_APPID,
                    "secret": settings.WECHAT_MINIAPP_SECRET,
                    "js_code": validated_data["code"],
                    "grant_type": "authorization_code",
                },
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            self.fail("wechat_unreachable")

        if payload.get("errcode"):
            self.fail("wechat_code_invalid")

        openid = payload.get("openid")
        if not isinstance(openid, str) or not openid:
            self.fail("wechat_openid_missing")

        return self._build_login_payload(openid, f"微信用户{openid[-6:]}")
