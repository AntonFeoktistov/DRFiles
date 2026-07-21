from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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

        resource = self.storage.get_resource(user=request.user.id, path=path)

        response_serializer = ResourceResponseSerializer(resource)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(request=upload_request, parameters=upload_parameters)
    def post(self, request):
        object = request.FILES.getlist("object") if request.FILES else []

        if not object:
            return Response(
                {"detail": "No files provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        path = request.query_params.get("path", "")

        try:
            uploaded = self.storage.upload_files(
                user_id=request.user.id, path=path, files=object
            )

            return Response(uploaded, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except FileNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
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

        try:
            self.storage.delete_resource(user_id=request.user.id, path=path)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FileNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
