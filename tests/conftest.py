import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from storage.models import Folder
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
def test_user_2(user_model):
    return user_model.objects.create_user(
        username=TEST_USERNAME + "2",
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


@pytest.fixture
def make_test_file():
    def _make_test_file(
        name: str = "test.txt", content: str = "Hello World", encoding: str = "utf-8"
    ):
        return SimpleUploadedFile(
            name=name,
            content=content.encode(encoding),
            content_type="text/plain",
        )

    return _make_test_file


@pytest.fixture
def make_test_folder(test_user):
    def _make_test_folder(name: str = "testfolder", parent=None):
        if parent:
            full_path = f"{parent.full_path}{name}/"
        else:
            full_path = f"{name}/"

        folder = Folder.objects.create(
            user=test_user, name=name, folder=parent, full_path=full_path
        )
        return folder

    return _make_test_folder


def make_auth_client_2(client, test_user_2):
    response = client.post(
        urls.login_url,
        {"username": TEST_USERNAME + "2", "password": TEST_PASSWORD},
        format="json",
    )
    access_token = response.json()["access"]

    auth_client = APIClient()
    auth_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return auth_client
