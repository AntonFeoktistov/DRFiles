from django.contrib.auth import login, logout
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from storage.services.repository import StorageRepository

from .serializers import LoginSerializer, RegisterSerializer


@extend_schema(request=RegisterSerializer)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        repo = StorageRepository()
        repo.get_or_create_root_folder(user.id)
        login(request, user)
        return Response({"username": user.username}, status=status.HTTP_201_CREATED)


@extend_schema(request=LoginSerializer)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return Response({"username": user.username}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"username": request.user.username}, status=status.HTTP_200_OK)
