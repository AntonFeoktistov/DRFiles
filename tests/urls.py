from django.urls import reverse


class Urls:
    register_url = reverse("users:register")
    login_url = reverse("users:login")
    logout_url = reverse("users:logout")
    me_url = reverse("users:me")
    token_refresh_url = reverse("users:token_refresh")


urls = Urls()

TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass"
