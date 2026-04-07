from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from .models import ForumComment, ForumPost, ForumPostLike
from .serializers import ForumCommentSerializer, ForumPostSerializer


class ForumPostListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ForumPostSerializer
    queryset = ForumPost.objects.select_related("author").prefetch_related("comments", "likes")

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


class ForumPostDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ForumPostSerializer
    queryset = ForumPost.objects.select_related("author").prefetch_related("comments__author", "likes")


class MyForumPostsAPIView(generics.ListAPIView):
    serializer_class = ForumPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ForumPost.objects.select_related("author").prefetch_related("comments", "likes").filter(author=self.request.user)


class ForumCommentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ForumCommentSerializer
    queryset = ForumComment.objects.select_related("author", "post")

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        return self.queryset.filter(post_id=self.kwargs["post_id"], parent__isnull=True)

    def perform_create(self, serializer):
        post = ForumPost.objects.get(pk=self.kwargs["post_id"])
        serializer.save(author=self.request.user, post=post)


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
        post = ForumPost.objects.get(pk=post_id)
        like, created = ForumPostLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            return Response({"liked": False, "like_count": post.likes.count()}, status=status.HTTP_200_OK)
        return Response({"liked": True, "like_count": post.likes.count()}, status=status.HTTP_200_OK)
