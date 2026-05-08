from django.urls import path

from .views import (
    CurrentUserAPIView,
    EmailCodeRequestAPIView,
    LogoutAPIView,
    PairUpTokenObtainPairView,
    PairUpTokenRefreshView,
    RegisterAPIView,
    WechatLoginAPIView,
)


urlpatterns = [
    path("email-code/request/", EmailCodeRequestAPIView.as_view(), name="email-code-request"),
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", PairUpTokenObtainPairView.as_view(), name="login"),
    path("wechat-login/", WechatLoginAPIView.as_view(), name="wechat-login"),
    path("refresh/", PairUpTokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("me/", CurrentUserAPIView.as_view(), name="current-user"),
]
