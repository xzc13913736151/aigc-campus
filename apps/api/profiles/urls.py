from django.urls import path

from .views import MyProfileAPIView, MyProfileAvatarUploadAPIView, PublicProfileAPIView


urlpatterns = [
    path("me/", MyProfileAPIView.as_view(), name="my-profile"),
    path("me/avatar/", MyProfileAvatarUploadAPIView.as_view(), name="my-profile-avatar-upload"),
    path("users/<uuid:user_id>/", PublicProfileAPIView.as_view(), name="public-profile"),
]
