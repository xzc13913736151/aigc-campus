from django.urls import path

from .views import (
    ForumCommentLikeToggleAPIView,
    ForumCommentListCreateAPIView,
    ForumPostDetailAPIView,
    ForumPostImageCreateAPIView,
    ForumPostLikeToggleAPIView,
    ForumPostListCreateAPIView,
    MyForumPostsAPIView,
)


urlpatterns = [
    path("posts/", ForumPostListCreateAPIView.as_view(), name="forum-post-list"),
    path("posts/mine/", MyForumPostsAPIView.as_view(), name="forum-post-mine"),
    path("posts/<uuid:pk>/", ForumPostDetailAPIView.as_view(), name="forum-post-detail"),
    path("posts/<uuid:post_id>/comments/", ForumCommentListCreateAPIView.as_view(), name="forum-comment-list"),
    path("posts/<uuid:post_id>/images/", ForumPostImageCreateAPIView.as_view(), name="forum-post-image-create"),
    path("posts/<uuid:post_id>/like/", ForumPostLikeToggleAPIView.as_view(), name="forum-post-like"),
    path("comments/<uuid:comment_id>/like/", ForumCommentLikeToggleAPIView.as_view(), name="forum-comment-like"),
    path("comment-likes/<uuid:comment_id>/", ForumCommentLikeToggleAPIView.as_view(), name="forum-comment-like-alias"),
]
