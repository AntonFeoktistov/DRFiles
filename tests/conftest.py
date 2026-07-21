import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from tests.urls import TEST_PASSWORD, TEST_USERNAME, urls


@pytest.fixture
def user_model():
    return get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def test_user(user_model):
    return user_model.objects.create_user(
        username=TEST_USERNAME,
        password=TEST_PASSWORD,
    )


@pytest.fixture
def auth_client(client, test_user):
    response = client.post(
        urls.login_url,
        {"username": TEST_USERNAME, "password": TEST_PASSWORD},
        format="json",
    )
    access_token = response.json()["access"]

    auth_client = APIClient()
    auth_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return auth_client
