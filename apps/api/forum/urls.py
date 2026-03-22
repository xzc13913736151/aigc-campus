from django.urls import path

from .views import ForumCommentListCreateAPIView, ForumPostDetailAPIView, ForumPostLikeToggleAPIView, ForumPostListCreateAPIView, MyForumPostsAPIView


urlpatterns = [
    path("posts/", ForumPostListCreateAPIView.as_view(), name="forum-post-list"),
    path("posts/mine/", MyForumPostsAPIView.as_view(), name="forum-post-mine"),
    path("posts/<uuid:pk>/", ForumPostDetailAPIView.as_view(), name="forum-post-detail"),
    path("posts/<uuid:post_id>/comments/", ForumCommentListCreateAPIView.as_view(), name="forum-comment-list"),
    path("posts/<uuid:post_id>/like/", ForumPostLikeToggleAPIView.as_view(), name="forum-post-like"),
]
