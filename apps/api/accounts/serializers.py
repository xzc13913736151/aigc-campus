from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import EmailVerificationCode


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "nickname",
            "role",
            "is_email_verified",
            "email_verified_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "role", "is_email_verified", "email_verified_at", "created_at", "updated_at")


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
