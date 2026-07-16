from django.urls import path

from .views import LoginView, LogoutView, MeView, RegisterView

app_name = "users"

urlpatterns = [
    path("sign-up", RegisterView.as_view(), name="register"),
    path("sign-in", LoginView.as_view(), name="login"),
    path("sign-out", LogoutView.as_view(), name="logout"),
    path("me", MeView.as_view(), name="me"),
]
