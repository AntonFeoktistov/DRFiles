from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, token = result
            jti = token["jti"]
            if cache.get(f"blacklist_{jti}"):
                raise InvalidToken("Token is blacklisted")
        return result
