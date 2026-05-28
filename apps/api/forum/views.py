from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, parsers, permissions, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer

from notifications.models import Notification
from notifications.services import create_notification

from .models import ForumComment, ForumCommentLike, ForumPost, ForumPostImage, ForumPostLike
from .serializers import ForumCommentSerializer, ForumPostImageSerializer, ForumPostSerializer


class IsForumPostAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id


class ForumPostListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ForumPostSerializer
    queryset = ForumPost.objects.select_related("author").prefetch_related("comments__author", "comments__replies__author", "likes", "images")

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = self.queryset.filter(is_deleted=False)
        query = self.request.query_params.get("q")
        category = self.request.query_params.get("category")
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(body__icontains=query))
        if category:
            queryset = queryset.filter(category__iexact=category)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ForumPostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ForumPostSerializer
    queryset = ForumPost.objects.select_related("author").prefetch_related("comments__author", "comments__replies__author", "likes", "images")

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsForumPostAuthor()]

    def get_queryset(self):
        if self.request.method in permissions.SAFE_METHODS:
            return self.queryset.filter(is_deleted=False)
        return self.queryset

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted", "updated_at"])


class MyForumPostsAPIView(generics.ListAPIView):
    serializer_class = ForumPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ForumPost.objects.select_related("author").prefetch_related("comments__author", "comments__replies__author", "likes", "images").filter(author=self.request.user)


class ForumCommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ForumCommentSerializer
    queryset = ForumComment.objects.select_related("author", "post", "parent").prefetch_related("replies__author")

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        return self.queryset.filter(post_id=self.kwargs["post_id"], parent__isnull=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["post"] = get_object_or_404(ForumPost, pk=self.kwargs["post_id"], is_deleted=False)
        return context

    def perform_create(self, serializer):
        post = get_object_or_404(ForumPost, pk=self.kwargs["post_id"], is_deleted=False)
        comment = serializer.save(author=self.request.user, post=post)

        if comment.parent_id:
            create_notification(
                recipient=comment.parent.author,
                actor=self.request.user,
                type=Notification.Type.FORUM_REPLY,
                title="你的评论收到回复",
                body=f"{self.request.user.nickname or self.request.user.email} 回复了你在《{post.title}》下的评论。",
                target_type="forum_post",
                target_id=str(post.id),
                extra={"post_id": str(post.id), "comment_id": str(comment.id)},
            )
        else:
            create_notification(
                recipient=post.author,
                actor=self.request.user,
                type=Notification.Type.FORUM_COMMENT,
                title="你的帖子收到评论",
                body=f"{self.request.user.nickname or self.request.user.email} 评论了《{post.title}》。",
                target_type="forum_post",
                target_id=str(post.id),
                extra={"post_id": str(post.id), "comment_id": str(comment.id)},
            )


class ForumPostLikeToggleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                name="ForumPostLikeToggleResponse",
                fields={
                    "liked": serializers.BooleanField(),
                    "like_count": serializers.IntegerField(),
                },
            ),
        },
    )
    def post(self, request, post_id):
        post = get_object_or_404(ForumPost, pk=post_id, is_deleted=False)
        like, created = ForumPostLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            return Response({"liked": False, "like_count": post.likes.count()}, status=status.HTTP_200_OK)
        create_notification(
            recipient=post.author,
            actor=request.user,
            type=Notification.Type.FORUM_LIKE,
            title="你的帖子收到点赞",
            body=f"{request.user.nickname or request.user.email} 点赞了《{post.title}》。",
            target_type="forum_post",
            target_id=str(post.id),
            extra={"post_id": str(post.id)},
        )
        return Response({"liked": True, "like_count": post.likes.count()}, status=status.HTTP_200_OK)


class ForumCommentLikeToggleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                name="ForumCommentLikeToggleResponse",
                fields={
                    "liked": serializers.BooleanField(),
                    "like_count": serializers.IntegerField(),
                },
            ),
        },
    )
    def post(self, request, comment_id):
        comment = get_object_or_404(ForumComment, pk=comment_id)
        like, created = ForumCommentLike.objects.get_or_create(comment=comment, user=request.user)
        if not created:
            like.delete()
            return Response({"liked": False, "like_count": comment.likes.count()}, status=status.HTTP_200_OK)
        create_notification(
            recipient=comment.author,
            actor=request.user,
            type=Notification.Type.FORUM_LIKE,
            title="你的评论收到点赞",
            body=f"{request.user.nickname or request.user.email} 点赞了你在《{comment.post.title}》下的评论。",
            target_type="forum_post",
            target_id=str(comment.post_id),
            extra={"post_id": str(comment.post_id), "comment_id": str(comment.id)},
        )
        return Response({"liked": True, "like_count": comment.likes.count()}, status=status.HTTP_200_OK)


class ForumPostImageCreateAPIView(generics.CreateAPIView):
    serializer_class = ForumPostImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def perform_create(self, serializer):
        post = get_object_or_404(ForumPost, pk=self.kwargs["post_id"], is_deleted=False)
        if post.author_id != self.request.user.id:
            raise PermissionDenied("You can only upload images to your own post.")
        serializer.save(post=post)
