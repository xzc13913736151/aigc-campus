from django.urls import path

from .views import BlockListCreateAPIView, ReportCreateAPIView


urlpatterns = [
    path("reports/", ReportCreateAPIView.as_view(), name="report-create"),
    path("blocks/", BlockListCreateAPIView.as_view(), name="block-list-create"),
]
