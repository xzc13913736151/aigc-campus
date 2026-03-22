from django.urls import path

from .views import CurrentUserAPIView, LogoutAPIView, PairUpTokenObtainPairView, PairUpTokenRefreshView, RegisterAPIView


urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", PairUpTokenObtainPairView.as_view(), name="login"),
    path("refresh/", PairUpTokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("me/", CurrentUserAPIView.as_view(), name="current-user"),
]
