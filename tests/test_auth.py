import pytest
from django.contrib.auth import get_user_model

from tests.urls import urls

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_register_success(client):
    response = client.post(
        urls.register_url,
        {"username": "newuser", "password": "pass123"},
        format="json",
    )
    assert response.status_code == 201
    assert response.json() == {"username": "newuser"}
    assert User.objects.filter(username="newuser").exists()


def test_register_duplicate_username(client, test_user):
    response = client.post(
        urls.register_url,
        {"username": "testuser", "password": "pass123"},
        format="json",
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["message"].lower()


def test_register_too_short_password(client):
    response = client.post(
        urls.register_url,
        {"username": "new_user", "password": "s"},
        format="json",
    )
    assert response.status_code == 400
    assert "message" in response.json()


def test_login_success(client, test_user):
    response = client.post(
        urls.login_url,
        {"username": test_user.username, "password": "testpass123"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json() == {"username": test_user.username}


def test_login_no_such_user(client):
    response = client.post(
        urls.login_url,
        {"username": "user_not_exists", "password": "random_pass"},
        format="json",
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["message"]


def test_login_not_correct_password(client, test_user):
    response = client.post(
        urls.login_url,
        {"username": test_user.username, "password": "not_correct_password"},
        format="json",
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["message"]


def test_login_empty_fields(client):
    response = client.post(
        urls.login_url,
        {},
        format="json",
    )
    assert response.status_code == 400
    assert "message" in response.json()


def test_logout_success(auth_client):
    response = auth_client.post(urls.logout_url)
    assert response.status_code == 204
    assert response.content == b""


def test_logout_not_auth(client):
    response = client.post(urls.logout_url)
    assert response.status_code == 401
    assert "credentials" in response.json()["message"].lower()


def test_me_success(auth_client, test_user):
    response = auth_client.get(urls.me_url)
    assert response.status_code == 200
    assert response.json() == {"username": test_user.username}


def test_me_not_auth(client):
    response = client.get(urls.me_url)
    assert response.status_code == 401
    assert "credentials" in response.json()["message"].lower()
