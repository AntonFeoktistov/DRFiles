from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from storage.services import path_utils
from storage.services.main_service import StorageService
from storage.spectacular.directory_params import (
    directory_get_parameters,
)

from ..serializers import (
    ResourceResponseSerializer,
)


class DirectoryView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = StorageService()

    @extend_schema(parameters=directory_get_parameters)
    def get(self, request):
        path = request.query_params.get("path", "")
        if not path_utils.is_resource_folder(path):
            raise ParseError(f"{path} is not valid folder path")

        resources = self.storage.get_folder_resources(request.user.id, path)
        response_serializer = ResourceResponseSerializer(resources, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(parameters=directory_get_parameters)
    def post(self, request):
        path = request.query_params.get("path", "")

        try:
            directory = self.storage.create_directory(request.user.id, path)
            response_serializer = ResourceResponseSerializer(directory)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
