from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/profile/", include("profiles.urls")),
    path("api/v1/teammates/", include("teammates.urls")),
    path("api/v1/dating/", include("dating.urls")),
    path("api/v1/forum/", include("forum.urls")),
    path("api/v1/moderation/", include("moderation.urls")),
]
