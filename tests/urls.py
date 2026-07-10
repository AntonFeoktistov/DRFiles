from django.urls import reverse


class Urls:
    register_url = reverse("users:register")
    login_url = reverse("users:login")
    logout_url = reverse("users:logout")
    me_url = reverse("users:me")


urls = Urls()
