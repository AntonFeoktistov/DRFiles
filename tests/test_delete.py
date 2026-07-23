import pytest
from django.contrib.auth import get_user_model

from storage.models import File, Folder
from storage.services.minio_service import MinioService
from tests import factory
from tests.conftest import make_auth_client_2

User = get_user_model()
pytestmark = pytest.mark.django_db
minio = MinioService()


# ==================== ТЕСТЫ УДАЛЕНИЯ ФАЙЛОВ ====================


def test_delete_file_success(auth_client, test_user, make_test_file):
    file = make_test_file(name="test1.txt")
    factory.upload_file(auth_client, file)

    response = auth_client.delete(
        "/api/resource?path=test1.txt",
        format="json",
    )
    assert response.status_code == 204
    assert not File.objects.filter(name=file.name, user=test_user).exists()
    assert not minio.is_file_exists(test_user.id, file.name)


def test_delete_file_not_exists(auth_client, test_user):
    response = auth_client.delete(
        "/api/resource?path=test1.txt",
        format="json",
    )
    assert response.status_code == 404


def test_delete_file_not_exists_but_another_user_has(
    auth_client, test_user, test_user_2, client, make_test_file
):
    file = make_test_file(name="test1.txt")
    factory.upload_file(auth_client, file)

    auth_client_2 = make_auth_client_2(client, test_user_2)
    response = auth_client_2.delete(
        "/api/resource?path=test1.txt",
        format="json",
    )
    assert response.status_code == 404
    assert File.objects.filter(name=file.name, user=test_user).exists()
    assert minio.is_file_exists(test_user.id, file.name)


def test_delete_file_not_auth(client, test_user):
    response = client.delete(
        "/api/resource?path=test1.txt",
        format="json",
    )
    assert response.status_code == 401


def test_delete_file_not_valid_path(auth_client, test_user):
    response = auth_client.delete(
        "/api/resource?path=",
        format="json",
    )
    assert response.status_code == 400


# ==================== ТЕСТЫ УДАЛЕНИЯ ПАПОК ====================


def test_delete_empty_folder_success(auth_client, test_user, make_test_folder):
    folder = make_test_folder(name="testfolder")
    auth_client.post(f"/api/directory?path={folder.full_path}", format="json")

    response = auth_client.delete(
        f"/api/resource?path={folder.full_path}",
        format="json",
    )
    assert response.status_code == 204
    assert not Folder.objects.filter(name=folder.name, user=test_user).exists()


def test_delete_folder_with_files_success(
    auth_client, test_user, make_test_folder, make_test_file
):
    folder = make_test_folder(name="testfolder")
    auth_client.post(f"/api/directory?path={folder.full_path}", format="json")

    file1 = make_test_file(name="test1.txt")
    file2 = make_test_file(name="test2.txt")
    factory.upload_file(auth_client, file1, path="testfolder/")
    factory.upload_file(auth_client, file2, path="testfolder/")

    assert File.objects.filter(user=test_user, folder=folder).count() == 2
    assert minio.is_file_exists(test_user.id, "testfolder/test1.txt")
    assert minio.is_file_exists(test_user.id, "testfolder/test2.txt")

    response = auth_client.delete(
        f"/api/resource?path={folder.full_path}",
        format="json",
    )
    assert response.status_code == 204

    assert not Folder.objects.filter(name=folder.name, user=test_user).exists()

    assert not File.objects.filter(user=test_user, folder=folder).exists()
    assert (
        File.objects.filter(user=test_user, full_path__startswith="testfolder/").count()
        == 0
    )
    assert not minio.is_file_exists(test_user.id, "testfolder/test1.txt")
    assert not minio.is_file_exists(test_user.id, "testfolder/test2.txt")


def test_delete_nested_folder_success(
    auth_client, test_user, make_test_folder, make_test_file
):
    parent = make_test_folder(name="parent")
    auth_client.post(f"/api/directory?path={parent.full_path}", format="json")

    child = make_test_folder(name="child", parent=parent)
    auth_client.post(f"/api/directory?path={child.full_path}", format="json")

    file = make_test_file(name="test.txt")
    factory.upload_file(auth_client, file, path="parent/child/")

    assert Folder.objects.filter(user=test_user, full_path="parent/").exists()
    assert Folder.objects.filter(user=test_user, full_path="parent/child/").exists()
    assert File.objects.filter(
        user=test_user, full_path="parent/child/test.txt"
    ).exists()

    response = auth_client.delete(
        "/api/resource?path=parent/child/",
        format="json",
    )
    assert response.status_code == 204

    assert not Folder.objects.filter(user=test_user, full_path="parent/child/").exists()

    assert not File.objects.filter(
        user=test_user, full_path="parent/child/test.txt"
    ).exists()
    assert not minio.is_file_exists(test_user.id, "parent/child/test.txt")

    assert Folder.objects.filter(user=test_user, full_path="parent/").exists()


def test_delete_folder_not_exists(auth_client, test_user):
    response = auth_client.delete(
        "/api/resource?path=notexists/",
        format="json",
    )
    assert response.status_code == 404


def test_delete_folder_not_exists_but_another_user_has(
    auth_client, test_user, test_user_2, client, make_test_folder
):
    folder = make_test_folder(name="testfolder")
    auth_client.post(f"/api/directory?path={folder.full_path}", format="json")

    auth_client_2 = make_auth_client_2(client, test_user_2)
    response = auth_client_2.delete(
        f"/api/resource?path={folder.full_path}",
        format="json",
    )
    assert response.status_code == 404
    assert Folder.objects.filter(name=folder.name, user=test_user).exists()


def test_delete_folder_not_auth(client, test_user):
    response = client.delete(
        "/api/resource?path=testfolder/",
        format="json",
    )
    assert response.status_code == 401


def test_delete_folder_not_valid_path(auth_client, test_user):
    response = auth_client.delete(
        "/api/resource?path=",
        format="json",
    )
    assert response.status_code == 400


def test_delete_root_folder_success(auth_client, test_user, make_test_file):
    file1 = make_test_file(name="file1.txt")
    file2 = make_test_file(name="file2.txt")
    factory.upload_file(auth_client, file1)
    factory.upload_file(auth_client, file2)

    assert File.objects.filter(user=test_user).count() == 2

    response = auth_client.delete(
        "/api/resource?path=",
        format="json",
    )
    assert response.status_code in [400, 404]

    root_folder = Folder.objects.filter(user=test_user, full_path="").first()
    assert root_folder is not None

    assert File.objects.filter(user=test_user).count() == 2
