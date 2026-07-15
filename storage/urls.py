from django.urls import path

from storage.views.download_view import ResourceDownloadView
from storage.views.resource_view import ResourceView

app_name = "users"

urlpatterns = [
    path("resource/download/", ResourceDownloadView.as_view(), name="download"),
    path("resource/", ResourceView.as_view(), name="resource"),
]
