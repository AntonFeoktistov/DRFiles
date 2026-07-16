from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from storage.services.main_service import StorageService
from storage.spectacular.search_params import search_parameters

from ..serializers import (
    ResourceResponseSerializer,
)


@method_decorator(csrf_exempt, name="dispatch")
class ResourceSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = StorageService()

    @extend_schema(parameters=search_parameters)
    def get(self, request):
        query = request.query_params.get("query", "")
        if not query:
            raise ParseError(f"{query} is not valid search query")
        resources = self.storage.search_resources(request.user.id, query)
        response_serializer = ResourceResponseSerializer(resources, many=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
