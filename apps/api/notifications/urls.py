from django.urls import path

from .views import (
    NotificationDetailAPIView,
    NotificationListAPIView,
    NotificationMarkAllReadAPIView,
    NotificationUnreadCountAPIView,
)


urlpatterns = [
    path("", NotificationListAPIView.as_view(), name="notification-list"),
    path("unread-count/", NotificationUnreadCountAPIView.as_view(), name="notification-unread-count"),
    path("mark-all-read/", NotificationMarkAllReadAPIView.as_view(), name="notification-mark-all-read"),
    path("<uuid:pk>/", NotificationDetailAPIView.as_view(), name="notification-detail"),
]
