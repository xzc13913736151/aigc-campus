from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def healthcheck(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", healthcheck, name="health"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/profile/", include("profiles.urls")),
    path("api/v1/assistant/", include("assistant.urls")),
    path("api/v1/teammates/", include("teammates.urls")),
    path("api/v1/dating/", include("dating.urls")),
    path("api/v1/chat/", include("chat.urls")),
    path("api/v1/forum/", include("forum.urls")),
    path("api/v1/notifications/", include("notifications.urls")),
    path("api/v1/trade/", include("trade.urls")),
    path("api/v1/moderation/", include("moderation.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
