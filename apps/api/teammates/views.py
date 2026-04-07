from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import TeamApplication, TeamPost
from .serializers import (
    TeamApplicationCreateSerializer,
    TeamApplicationReviewSerializer,
    TeamApplicationSerializer,
    TeamPostSerializer,
)


class TeamPostListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TeamPostSerializer
    queryset = TeamPost.objects.select_related("author")

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = self.queryset
        query = self.request.query_params.get("q")
        tag = self.request.query_params.get("tag")
        status_filter = self.request.query_params.get("status")

        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(details__icontains=query))
        if tag:
            queryset = queryset.filter(Q(title__icontains=tag) | Q(summary__icontains=tag) | Q(details__icontains=tag))
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TeamPostDetailAPIView(generics.RetrieveAPIView):
    serializer_class = TeamPostSerializer
    queryset = TeamPost.objects.select_related("author")


class MyTeamPostsAPIView(generics.ListAPIView):
    serializer_class = TeamPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TeamPost.objects.select_related("author").filter(author=self.request.user)


class TeamApplicationCreateAPIView(generics.CreateAPIView):
    serializer_class = TeamApplicationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        post = get_object_or_404(TeamPost, pk=self.kwargs["post_id"])
        if post.author_id == self.request.user.id:
            raise PermissionDenied("You cannot apply to your own post.")
        serializer.instance = TeamApplication.objects.create(post=post, applicant=self.request.user, **serializer.validated_data)


class MyApplicationsAPIView(generics.ListAPIView):
    serializer_class = TeamApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TeamApplication.objects.select_related("post", "applicant", "post__author").filter(applicant=self.request.user)


class ReceivedApplicationsAPIView(generics.ListAPIView):
    serializer_class = TeamApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TeamApplication.objects.select_related("post", "applicant", "post__author").filter(post__author=self.request.user)


class TeamApplicationReviewAPIView(generics.UpdateAPIView):
    serializer_class = TeamApplicationReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TeamApplication.objects.select_related("post", "applicant", "post__author")

    def perform_update(self, serializer):
        application = self.get_object()
        if application.post.author_id != self.request.user.id:
            raise PermissionDenied("You can only manage applications for your own post.")

        updated_application = serializer.save()
        post = updated_application.post
        if updated_application.status == TeamApplication.Status.ACCEPTED:
            post.current_size = min(post.current_size + 1, post.target_size)
            if post.current_size >= post.target_size:
                post.status = TeamPost.Status.FILLED
            post.save(update_fields=["current_size", "status", "updated_at"])
