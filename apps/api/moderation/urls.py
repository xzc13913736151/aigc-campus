from django.urls import path

from .views import (
    AdminModerationActionLogListAPIView,
    AdminReportDetailAPIView,
    AdminReportListAPIView,
    AdminReportStatsAPIView,
    BlockDeleteAPIView,
    BlockListCreateAPIView,
    ReportCreateAPIView,
)


urlpatterns = [
    path("reports/", ReportCreateAPIView.as_view(), name="report-create"),
    path("admin/reports/", AdminReportListAPIView.as_view(), name="admin-report-list"),
    path("admin/reports/stats/", AdminReportStatsAPIView.as_view(), name="admin-report-stats"),
    path("admin/reports/<uuid:pk>/", AdminReportDetailAPIView.as_view(), name="admin-report-detail"),
    path("admin/action-logs/", AdminModerationActionLogListAPIView.as_view(), name="admin-moderation-action-logs"),
    path("blocks/", BlockListCreateAPIView.as_view(), name="block-list-create"),
    path("blocks/<uuid:pk>/", BlockDeleteAPIView.as_view(), name="block-delete"),
]
