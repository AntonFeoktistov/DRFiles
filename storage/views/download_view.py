from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from storage.services.main_service import StorageService
from storage.spectacular.download_params import download_parameters


class ResourceDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = StorageService()

    @extend_schema(parameters=download_parameters)
    def get(self, request):
        path = request.query_params.get("path", "")
        return self.storage.download_resource(request.user.id, path)
