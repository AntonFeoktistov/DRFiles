from django.urls import path

from storage.views import ResourceView

app_name = "users"

urlpatterns = [
    path("resource/", ResourceView.as_view(), name="resource"),
]
