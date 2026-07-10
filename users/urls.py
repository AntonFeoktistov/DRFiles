from django.urls import path

from .views import HealthCheckView, LoginView, LogoutView, RegisterView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me", HealthCheckView.as_view(), name="health_check"),
]
