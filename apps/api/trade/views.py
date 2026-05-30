from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import TradeFavorite, TradeMatch, TradePost
from .serializers import (
    TradeFavoriteSerializer,
    TradeMatchSerializer,
    TradePostCreateSerializer,
    TradePostSerializer,
    TradePostStatusUpdateSerializer,
)


class IsTradePostAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id


class TradePostListCreateAPIView(generics.ListCreateAPIView):
    queryset = TradePost.objects.select_related("author")

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TradePostCreateSerializer
        return TradePostSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(status=TradePost.Status.OPEN)
        query = self.request.query_params.get("q")
        post_type = self.request.query_params.get("type")
        tag = self.request.query_params.get("tag")

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query) | Q(condition__icontains=query)
            )
        if post_type:
            queryset = queryset.filter(post_type=post_type)
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
        return queryset.order_by("-is_highlighted", "-bump_score", "-created_at")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TradePostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TradePost.objects.select_related("author")

    def get_serializer_class(self):
        if self.request.method == "PATCH" and set(self.request.data.keys()) <= {"status"}:
            return TradePostStatusUpdateSerializer
        return TradePostSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsTradePostAuthor()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.view_count += 1
        instance.save(update_fields=["view_count"])
        return super().retrieve(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        instance = self.get_object()
        return Response(TradePostSerializer(instance, context=self.get_serializer_context()).data, status=response.status_code)


class MyTradePostsAPIView(generics.ListAPIView):
    serializer_class = TradePostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TradePost.objects.select_related("author").filter(author=self.request.user)


class TradeFavoriteCreateDestroyAPIView(generics.CreateAPIView, generics.DestroyAPIView):
    serializer_class = TradeFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TradeFavorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        post = get_object_or_404(TradePost, pk=self.kwargs["post_id"])
        if post.author_id == self.request.user.id:
            raise PermissionDenied("You cannot favorite your own post.")
        favorite, _ = TradeFavorite.objects.get_or_create(user=self.request.user, post=post)
        serializer.instance = favorite

    def delete(self, request, *args, **kwargs):
        post = get_object_or_404(TradePost, pk=self.kwargs["post_id"])
        TradeFavorite.objects.filter(user=request.user, post=post).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyTradeMatchesAPIView(generics.ListAPIView):
    serializer_class = TradeMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            TradeMatch.objects.select_related("user_a", "user_b", "related_post")
            .filter(Q(user_a=self.request.user) | Q(user_b=self.request.user))
            .order_by("-created_at")
        )
