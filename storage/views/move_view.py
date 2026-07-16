from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from storage.services.main_service import StorageService
from storage.spectacular.move_params import move_parameters

from ..serializers import (
    ResourceResponseSerializer,
)


@method_decorator(csrf_exempt, name="dispatch")
class ResourceMoveView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = StorageService()

    @extend_schema(parameters=move_parameters)
    def post(self, request):
        path_from = request.query_params.get("from", "")
        path_to = request.query_params.get("to", "")

        try:
            resource = self.storage.move_resource(request.user.id, path_from, path_to)
            response_serializer = ResourceResponseSerializer(resource)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
