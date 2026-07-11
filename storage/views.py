from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from storage.services.storage_service import StorageService

from .serializers import (
    ResourceGetSerializer,
    ResourceResponseSerializer,
)


class ResourceView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = StorageService()

    @extend_schema(
        parameters=[ResourceGetSerializer], responses=ResourceResponseSerializer
    )
    def get(self, request):
        serializer = ResourceGetSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        path = serializer.validated_data.get("path", "")

        resource = self.storage.get_resource(user=request.user, path=path)

        response_serializer = ResourceResponseSerializer(resource)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    # @extend_schema(request=ResourceCreateSerializer)
    # def post(self, request):
    #     serializer = ResourceCreateSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)

    #     validated_data = serializer.validated_data
    #     user = request.user

    #     if validated_data['type'] == 'FOLDER':
    #         resource = self.storage.create_folder(
    #             user=user,
    #             path=validated_data.get('path', ''),
    #             name=validated_data['name']
    #         )
    #     else:
    #         resource = self.storage.upload_file(
    #             user=user,
    #             path=validated_data.get('path', ''),
    #             name=validated_data['name'],
    #             file_obj=validated_data['file']
    #         )

    #     response_serializer = ResourceResponseSerializer(resource)
    #     return Response(
    #         response_serializer.data,
    #         status=status.HTTP_201_CREATED
    #     )
