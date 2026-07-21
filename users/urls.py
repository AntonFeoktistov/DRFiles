from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import LoginView, LogoutView, MeView, RegisterView

app_name = "users"

urlpatterns = [
    path("sign-up", RegisterView.as_view(), name="register"),
    path("sign-in", LoginView.as_view(), name="login"),
    path("sign-out", LogoutView.as_view(), name="logout"),
    path("me", MeView.as_view(), name="me"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]
