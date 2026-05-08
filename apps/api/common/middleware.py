from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


User = get_user_model()


class QueryStringJWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        token = self._get_token(scope)
        scope["user"] = await self._get_user(token)
        return await self.inner(scope, receive, send)

    def _get_token(self, scope):
        query_string = parse_qs(scope.get("query_string", b"").decode())
        return query_string.get("token", [None])[0]

    @database_sync_to_async
    def _get_user(self, token):
        if not token:
            return AnonymousUser()
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
        except (InvalidToken, TokenError, KeyError):
            return AnonymousUser()

        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()
