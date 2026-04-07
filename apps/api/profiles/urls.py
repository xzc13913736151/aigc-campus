from django.urls import path

from .views import MyProfileAPIView, PublicProfileAPIView


urlpatterns = [
    path("me/", MyProfileAPIView.as_view(), name="my-profile"),
    path("users/<uuid:user_id>/", PublicProfileAPIView.as_view(), name="public-profile"),
]
