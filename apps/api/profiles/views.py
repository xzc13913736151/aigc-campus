from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import generics, parsers, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.uploads import validate_uploaded_image

from .models import Profile
from .serializers import ProfileSerializer


class MyProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


class MyProfileAvatarUploadAPIView(generics.GenericAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request, *args, **kwargs):
        profile = request.user.profile
        upload = request.FILES.get("file")
        try:
            validate_uploaded_image(upload, max_size=3 * 1024 * 1024, label="头像")
        except ValidationError as exc:
            detail = exc.detail[0] if isinstance(exc.detail, list) else exc.detail
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)

        extension = Path(upload.name).suffix.lower() or ".png"
        saved_path = default_storage.save(f"avatars/{request.user.id}/{uuid4().hex}{extension}", upload)
        profile.avatar_url = request.build_absolute_uri(settings.MEDIA_URL + saved_path)
        profile.save(update_fields=["avatar_url", "updated_at"])

        return Response(ProfileSerializer(profile, context=self.get_serializer_context()).data, status=status.HTTP_200_OK)


class PublicProfileAPIView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Profile.objects.select_related("user")
    lookup_field = "user_id"
