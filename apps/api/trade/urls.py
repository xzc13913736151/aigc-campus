from django.urls import path

from .views import (
    MyTradeMatchesAPIView,
    MyTradePostsAPIView,
    TradeFavoriteCreateDestroyAPIView,
    TradePostDetailAPIView,
    TradePostListCreateAPIView,
)

urlpatterns = [
    path("posts/", TradePostListCreateAPIView.as_view(), name="trade-posts"),
    path("posts/<uuid:pk>/", TradePostDetailAPIView.as_view(), name="trade-post-detail"),
    path("posts/mine/", MyTradePostsAPIView.as_view(), name="my-trade-posts"),
    path("posts/<uuid:post_id>/favorite/", TradeFavoriteCreateDestroyAPIView.as_view(), name="trade-favorite"),
    path("matches/", MyTradeMatchesAPIView.as_view(), name="trade-matches"),
]