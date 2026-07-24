import importlib
import os

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APIClient
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.postgres import PostgresContainer

from tests.urls import TEST_PASSWORD, TEST_USERNAME, urls

os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin")
os.environ.setdefault("MINIO_BUCKET_NAME", "user-files")
os.environ.setdefault("MINIO_USE_SSL", "false")


@pytest.fixture(scope="session")
def postgres_container():
    """Запускает PostgreSQL в Docker контейнере для тестов"""
    with PostgresContainer("postgres:15") as postgres:
        os.environ["POSTGRES_DB"] = postgres.dbname
        os.environ["POSTGRES_USER"] = postgres.username
        os.environ["POSTGRES_PASSWORD"] = postgres.password
        os.environ["POSTGRES_HOST"] = postgres.get_container_host_ip()
        os.environ["POSTGRES_PORT"] = str(postgres.get_exposed_port(5432))

        wait_for_logs(postgres, "database system is ready to accept connections")

        yield postgres


@pytest.fixture(scope="session")
def minio_container():
    """Запускает MinIO в Docker контейнере для тестов"""
    container = DockerContainer("minio/minio:latest")
    container.with_command("server /data --console-address :9001")
    container.with_exposed_ports(9000, 9001)
    container.with_env("MINIO_ROOT_USER", "minioadmin")
    container.with_env("MINIO_ROOT_PASSWORD", "minioadmin")

    container.start()

    wait_for_logs(container, "MinIO Object Storage Server")

    host = container.get_container_host_ip()
    port = container.get_exposed_port(9000)
    endpoint = f"{host}:{port}"

    os.environ["MINIO_ENDPOINT"] = endpoint
    os.environ["MINIO_ACCESS_KEY"] = "minioadmin"
    os.environ["MINIO_SECRET_KEY"] = "minioadmin"
    os.environ["MINIO_BUCKET_NAME"] = "user-files"
    os.environ["MINIO_USE_SSL"] = "false"

    import boto3
    from botocore.client import Config

    client = boto3.client(
        "s3",
        endpoint_url=f"http://{endpoint}",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        region_name="us-east-1",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

    bucket_name = "user-files"
    try:
        client.head_bucket(Bucket=bucket_name)
    except Exception:
        client.create_bucket(Bucket=bucket_name)

    from storage.services import minio_service

    importlib.reload(minio_service)

    yield container

    container.stop()


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """Настраивает Django для работы с Testcontainers"""
    with django_db_blocker.unblock():
        call_command("migrate", verbosity=0)

        from storage.services.minio_service import MinioService

        minio_service = MinioService()
        minio_service._ensure_bucket_exists()


# ==================== STANDARD FIXTURES ====================


@pytest.fixture(scope="function")
def user_model():
    return get_user_model()


@pytest.fixture(scope="function")
def client():
    return APIClient()


@pytest.fixture(scope="function")
def test_user(user_model):
    return user_model.objects.create_user(
        username=TEST_USERNAME,
        password=TEST_PASSWORD,
    )


@pytest.fixture(scope="function")
def test_user_2(user_model):
    return user_model.objects.create_user(
        username=TEST_USERNAME + "2",
        password=TEST_PASSWORD,
    )


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def make_test_file():
    def _make_test_file(
        name: str = "test.txt", content="Hello World", encoding: str = "utf-8"
    ):
        if isinstance(content, str):
            content = content.encode(encoding)
        return SimpleUploadedFile(
            name=name,
            content=content,
            content_type="text/plain",
        )

    return _make_test_file


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


# ==================== АВТОМАТИЧЕСКИЙ ЗАПУСК КОНТЕЙНЕРОВ ====================


@pytest.fixture(scope="session", autouse=True)
def setup_test_containers(postgres_container, minio_container):
    pass
