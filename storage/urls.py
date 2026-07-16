from django.urls import path

from storage.views.directory_view import DirectoryView
from storage.views.download_view import ResourceDownloadView
from storage.views.move_view import ResourceMoveView
from storage.views.resource_view import ResourceView
from storage.views.search_view import ResourceSearchView

app_name = "users"

urlpatterns = [
    path("resource/download/", ResourceDownloadView.as_view(), name="download"),
    path("resource/move/", ResourceMoveView.as_view(), name="move"),
    path("resource/search/", ResourceSearchView.as_view(), name="search"),
    path("resource/", ResourceView.as_view(), name="resource"),
    path("directory/", DirectoryView.as_view(), name="directory"),
]
