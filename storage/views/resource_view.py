import json
import traceback

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.exceptions import ConflictError
from storage.services.main_service import StorageService
from storage.spectacular.delete_params import delete_parameters
from storage.spectacular.upload_params import upload_parameters, upload_request

from ..serializers import (
    ResourceGetSerializer,
    ResourceResponseSerializer,
)


class ResourceView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = StorageService()

    @extend_schema(request=upload_request, parameters=upload_parameters)
    def get(self, request):

        serializer = ResourceGetSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        path = serializer.validated_data.get("path", "")

        try:
            resource = self.storage.get_resource(request.user.id, path)
            if not resource:
                return Response(
                    {"detail": "Resource is not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            response_serializer = ResourceResponseSerializer(resource)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(parameters=delete_parameters)
    def delete(self, request):
        path = request.query_params.get("path")

        if not path:
            return Response(
                {"detail": "Path is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        self.storage.delete_resource(user_id=request.user.id, path=path)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=upload_request, parameters=upload_parameters)
    def post(self, request):

        files = request.FILES.getlist("object") if request.FILES else []
        if not files:
            return self._error_response(
                "No files provided", status.HTTP_400_BAD_REQUEST
            )

        paths = self._validate_paths(request, files)
        if isinstance(paths, Response):
            return paths
        files_with_paths = list(zip(files, paths))
        base_path = request.query_params.get("path", "")

        try:
            uploaded = self.storage.upload_resources(
                user_id=request.user.id,
                base_path=base_path,
                files_with_paths=files_with_paths,
            )
            return Response(uploaded, status=status.HTTP_201_CREATED)
        except ConflictError as e:
            return self._error_response(str(e), status.HTTP_409_CONFLICT)

        except Exception as e:
            return self._error_response(
                f"Internal server error: {str(e)}",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _validate_paths(self, request, files: list):
        paths = self._extract_paths_from_request(request)
        if not paths:
            paths = [file.name for file in files]
        if not len(files) == len(paths):
            return self._error_response(
                f"Number of files ({len(files)}) must match number of paths ({len(paths)})",
                status.HTTP_400_BAD_REQUEST,
            )

        return paths

    def _extract_paths_from_request(self, request) -> list:
        paths_data = request.POST.get("paths", "[]")

        try:
            if isinstance(paths_data, str):
                return json.loads(paths_data)
            return paths_data
        except json.JSONDecodeError:
            return []

    def _error_response(self, detail: str, status_code: int) -> Response:
        return Response({"detail": detail}, status=status_code)
