import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from tests.urls import TEST_PASSWORD, TEST_USERNAME, urls

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_register_success(client):
    response = client.post(
        urls.register_url,
        {"username": "newuser", "password": "pass123"},
        format="json",
    )
    assert response.status_code == 201

    data = response.json()
    assert "access" in data
    assert "refresh" in data
    assert data["username"] == "newuser"
    assert User.objects.filter(username="newuser").exists()


def test_register_duplicate_username(client, test_user):
    response = client.post(
        urls.register_url,
        {"username": TEST_USERNAME, "password": TEST_PASSWORD},
        format="json",
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_register_too_short_password(client):
    response = client.post(
        urls.register_url,
        {"username": "new_user", "password": "s"},
        format="json",
    )
    assert response.status_code == 400
    assert "password" in response.json()


def test_login_success(client, test_user):
    response = client.post(
        urls.login_url,
        {"username": TEST_USERNAME, "password": TEST_PASSWORD},
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert "access" in data
    assert "refresh" in data
    assert data["username"] == TEST_USERNAME


def test_login_no_such_user(client):
    response = client.post(
        urls.login_url,
        {"username": "user_not_exists", "password": "random_pass"},
        format="json",
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_not_correct_password(client, test_user):
    response = client.post(
        urls.login_url,
        {"username": TEST_USERNAME, "password": "not_correct_password"},
        format="json",
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_empty_fields(client):
    response = client.post(
        urls.login_url,
        {},
        format="json",
    )
    assert response.status_code == 400
    assert "username" in response.json()


def test_logout_success(client, test_user):
    response = client.post(
        urls.login_url,
        {"username": TEST_USERNAME, "password": TEST_PASSWORD},
        format="json",
    )
    refresh_token = response.json()["refresh"]
    access_token = response.json()["access"]

    auth_client = APIClient()
    auth_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    response = auth_client.post(
        urls.logout_url,
        {"refresh": refresh_token},
        format="json",
    )
    assert response.status_code == 204
    assert response.content == b""


def test_logout_not_auth(client):
    response = client.post(urls.logout_url)
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()


def test_me_success(auth_client, test_user):
    response = auth_client.get(urls.me_url)
    assert response.status_code == 200
    assert response.json() == {"username": test_user.username}


def test_me_not_auth(client):
    response = client.get(urls.me_url)
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()


def test_access_token_expired(client, test_user):
    response = client.post(
        urls.login_url,
        {"username": TEST_USERNAME, "password": TEST_PASSWORD},
        format="json",
    )
    access_token = response.json()["access"]

    # Подменяем токен на заведомо невалидный
    invalid_client = APIClient()
    invalid_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")

    response = invalid_client.get(urls.me_url)
    assert response.status_code == 401


def test_refresh_token_flow(client, test_user):
    response = client.post(
        urls.login_url,
        {"username": TEST_USERNAME, "password": TEST_PASSWORD},
        format="json",
    )
    refresh_token = response.json()["refresh"]

    response = client.post(
        urls.token_refresh_url,
        {"refresh": refresh_token},
        format="json",
    )
    assert response.status_code == 200
    assert "access" in response.json()
