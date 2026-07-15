from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from storage.services.main_service import StorageService
from storage.spectacular.download_params import download_parameters, download_responses


class ResourceDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = StorageService()

    @extend_schema(
        parameters=download_parameters,
        responses=download_responses,
    )
    def get(self, request):
        path = request.query_params.get("path", "")

        try:
            return self.storage.download_resource(request.user.id, path)
        except FileNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
