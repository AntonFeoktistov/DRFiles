import pytest
from django.contrib.auth import get_user_model

from tests import factory

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_get_file_success(auth_client, test_user, make_test_file):
    file = make_test_file(name="test1.txt")
    factory.upload_file(auth_client, file)
    response = auth_client.get(
        "/api/resource?path=test1.txt",
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    factory.assert_file_response_data(data, "", file.name)


def test_get_file_not_auth(auth_client, client, test_user, make_test_file):
    file = make_test_file(name="test1.txt")
    factory.upload_file(auth_client, file)

    response = client.get(
        "/api/resource?path=test1.txt",
        format="json",
    )
    assert response.status_code == 401


def test_get_file_not_exists(auth_client, test_user, make_test_file):
    file = make_test_file(name="test1.txt")
    factory.upload_file(auth_client, file)

    response = auth_client.get(
        "/api/resource?path=NOT_EXISTS.txt",
        format="json",
    )
    assert response.status_code == 404


def test_get_folder_success(auth_client, test_user):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")
    auth_client.post(f"/api/directory?path={folder.full_path}", format="json")

    response = auth_client.get(
        "/api/resource?path=testfolder/",
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == ""
    assert data["name"] == "testfolder"
    assert "size" not in data
    assert data["type"] == "DIRECTORY"


def test_get_folder_not_exists(auth_client, test_user):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")
    auth_client.post(f"/api/directory?path={folder.full_path}", format="json")

    response = auth_client.get(
        "/api/resource?path=NOTEXISTS/",
        format="json",
    )
    assert response.status_code == 404


def test_get_folder_resources_success(auth_client, test_user, make_test_file):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")

    file1 = make_test_file(name="test1.txt")
    file2 = make_test_file(name="test2.txt")
    factory.upload_file(auth_client, file1, path="testfolder/")
    factory.upload_file(auth_client, file2, path="testfolder/")

    response = auth_client.get(
        "/api/directory?path=testfolder/",
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    file_paths = [item["path"] + item["name"] for item in data]
    assert "testfolder/test1.txt" in file_paths
    assert "testfolder/test2.txt" in file_paths


def test_get_folder_resources_success_root_folder(
    auth_client, test_user, make_test_file
):
    file1 = make_test_file(name="test1.txt")
    file2 = make_test_file(name="test2.txt")
    factory.upload_file(auth_client, file1)
    factory.upload_file(auth_client, file2)

    response = auth_client.get(
        "/api/directory",
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    file_paths = [item["path"] + item["name"] for item in data]
    assert "test1.txt" in file_paths
    assert "test2.txt" in file_paths


def test_get_folder_resources_empty_folder(auth_client, test_user):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")
    auth_client.post(f"/api/directory?path={folder.full_path}", format="json")

    response = auth_client.get(
        "/api/directory?path=testfolder/",
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_get_folder_resources_not_auth(auth_client, client, test_user, make_test_file):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")

    file1 = make_test_file(name="test1.txt")
    factory.upload_file(auth_client, file1, path="testfolder/")

    response = client.get(
        "/api/directory?path=testfolder/",
        format="json",
    )
    assert response.status_code == 401


def test_get_folder_resources_not_exists(auth_client, test_user):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")
    auth_client.post(f"/api/directory?path={folder.full_path}", format="json")

    response = auth_client.get(
        "/api/directory?path=NOT_EXISTS/",
        format="json",
    )
    assert response.status_code == 404
