from django.urls import path

from .views import (
    MyApplicationsAPIView,
    MyTeamPostsAPIView,
    ReceivedApplicationsAPIView,
    TeamApplicationCreateAPIView,
    TeamApplicationReviewAPIView,
    TeamPostDetailAPIView,
    TeamPostListCreateAPIView,
)


urlpatterns = [
    path("posts/", TeamPostListCreateAPIView.as_view(), name="team-post-list"),
    path("posts/mine/", MyTeamPostsAPIView.as_view(), name="team-post-mine"),
    path("posts/<uuid:pk>/", TeamPostDetailAPIView.as_view(), name="team-post-detail"),
    path("posts/<uuid:post_id>/apply/", TeamApplicationCreateAPIView.as_view(), name="team-application-create"),
    path("applications/mine/", MyApplicationsAPIView.as_view(), name="team-application-mine"),
    path("applications/received/", ReceivedApplicationsAPIView.as_view(), name="team-application-received"),
    path("applications/<uuid:pk>/review/", TeamApplicationReviewAPIView.as_view(), name="team-application-review"),
]
