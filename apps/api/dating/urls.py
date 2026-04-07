from django.urls import path

from .views import DatingCandidateListAPIView, DatingMatchListAPIView, DatingPreferenceAPIView, DatingProfileAPIView, DatingSignalAPIView


urlpatterns = [
    path("profile/", DatingProfileAPIView.as_view(), name="dating-profile"),
    path("preferences/", DatingPreferenceAPIView.as_view(), name="dating-preferences"),
    path("candidates/", DatingCandidateListAPIView.as_view(), name="dating-candidates"),
    path("signals/", DatingSignalAPIView.as_view(), name="dating-signals"),
    path("matches/", DatingMatchListAPIView.as_view(), name="dating-matches"),
]
