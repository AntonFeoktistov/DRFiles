import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def user_model():
    return get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def test_user(user_model):
    return user_model.objects.create_user(
        username="testuser",
        password="testpass123",
    )


@pytest.fixture
def auth_client(client, test_user):
    client.login(username="testuser", password="testpass123")
    return client
