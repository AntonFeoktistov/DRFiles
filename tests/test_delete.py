import pytest
from django.contrib.auth import get_user_model

from storage.models import File, Folder
from tests import factory
from tests.conftest import make_auth_client_2

User = get_user_model()
pytestmark = pytest.mark.django_db


# ==================== ТЕСТЫ УДАЛЕНИЯ ФАЙЛОВ ====================


def test_delete_file_success(auth_client, test_user, make_test_file):
    file = make_test_file(name="test1.txt")
    factory.upload_file(auth_client, file)

    assert factory.is_file_exists_in_db(test_user, "test1.txt")
    assert factory.is_file_exists_in_minio(test_user, "test1.txt")

    response = auth_client.delete(
        "/api/resource?path=test1.txt",
        format="json",
    )
    assert response.status_code == 204

    assert not factory.is_file_exists_in_db(test_user, "test1.txt")
    assert not factory.is_file_exists_in_minio(test_user, "test1.txt")


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

    assert factory.is_file_exists_in_db(test_user, "test1.txt")
    assert factory.is_file_exists_in_minio(test_user, "test1.txt")

    auth_client_2 = make_auth_client_2(client, test_user_2)
    response = auth_client_2.delete(
        "/api/resource?path=test1.txt",
        format="json",
    )
    assert response.status_code == 404

    assert factory.is_file_exists_in_db(test_user, "test1.txt")
    assert factory.is_file_exists_in_minio(test_user, "test1.txt")

    assert not factory.is_file_exists_in_db(test_user_2, "test1.txt")
    assert not factory.is_file_exists_in_minio(test_user_2, "test1.txt")


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


def test_delete_empty_folder_success(auth_client, test_user):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")
    assert Folder.objects.filter(user=test_user, full_path="testfolder/").exists()

    response = auth_client.delete(
        f"/api/resource?path={folder.full_path}",
        format="json",
    )
    assert response.status_code == 204

    assert not Folder.objects.filter(user=test_user, full_path="testfolder/").exists()


def test_delete_folder_with_files_success(auth_client, test_user, make_test_file):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")

    file1 = make_test_file(name="test1.txt")
    file2 = make_test_file(name="test2.txt")
    factory.upload_file(auth_client, file1, path="testfolder/")
    factory.upload_file(auth_client, file2, path="testfolder/")

    assert factory.is_file_exists_in_db(test_user, "testfolder/test1.txt")
    assert factory.is_file_exists_in_db(test_user, "testfolder/test2.txt")
    assert factory.is_file_exists_in_minio(test_user, "testfolder/test1.txt")
    assert factory.is_file_exists_in_minio(test_user, "testfolder/test2.txt")
    assert File.objects.filter(user=test_user, folder=folder).count() == 2

    response = auth_client.delete(
        f"/api/resource?path={folder.full_path}",
        format="json",
    )
    assert response.status_code == 204

    assert not Folder.objects.filter(user=test_user, full_path="testfolder/").exists()

    assert not factory.is_file_exists_in_db(test_user, "testfolder/test1.txt")
    assert not factory.is_file_exists_in_db(test_user, "testfolder/test2.txt")
    assert not factory.is_file_exists_in_minio(test_user, "testfolder/test1.txt")
    assert not factory.is_file_exists_in_minio(test_user, "testfolder/test2.txt")
    assert File.objects.filter(user=test_user, folder=folder).count() == 0


def test_delete_nested_folder_success(auth_client, test_user, make_test_file):
    parent = factory.create_folder(auth_client, test_user, "parent/")
    child = factory.create_folder(auth_client, test_user, "parent/child/")

    file = make_test_file(name="test.txt")
    factory.upload_file(auth_client, file, path="parent/child/")

    assert Folder.objects.filter(user=test_user, full_path="parent/").exists()
    assert Folder.objects.filter(user=test_user, full_path="parent/child/").exists()
    assert factory.is_file_exists_in_db(test_user, "parent/child/test.txt")
    assert factory.is_file_exists_in_minio(test_user, "parent/child/test.txt")

    response = auth_client.delete(
        "/api/resource?path=parent/child/",
        format="json",
    )
    assert response.status_code == 204

    assert not Folder.objects.filter(user=test_user, full_path="parent/child/").exists()

    assert not factory.is_file_exists_in_db(test_user, "parent/child/test.txt")
    assert not factory.is_file_exists_in_minio(test_user, "parent/child/test.txt")

    assert Folder.objects.filter(user=test_user, full_path="parent/").exists()


def test_delete_folder_not_exists(auth_client, test_user):
    response = auth_client.delete(
        "/api/resource?path=notexists/",
        format="json",
    )
    assert response.status_code == 404


def test_delete_folder_not_exists_but_another_user_has(
    auth_client, test_user, test_user_2, client
):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")

    assert Folder.objects.filter(user=test_user, full_path="testfolder/").exists()

    auth_client_2 = make_auth_client_2(client, test_user_2)
    response = auth_client_2.delete(
        f"/api/resource?path={folder.full_path}",
        format="json",
    )
    assert response.status_code == 404

    assert Folder.objects.filter(user=test_user, full_path="testfolder/").exists()

    assert not Folder.objects.filter(user=test_user_2, full_path="testfolder/").exists()


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

    assert factory.is_file_exists_in_db(test_user, "file1.txt")
    assert factory.is_file_exists_in_db(test_user, "file2.txt")
    assert factory.is_file_exists_in_minio(test_user, "file1.txt")
    assert factory.is_file_exists_in_minio(test_user, "file2.txt")
    assert File.objects.filter(user=test_user).count() == 2

    response = auth_client.delete(
        "/api/resource?path=",
        format="json",
    )
    assert response.status_code in [400, 404]

    root_folder = Folder.objects.filter(user=test_user, full_path="").first()
    assert root_folder is not None

    assert factory.is_file_exists_in_db(test_user, "file1.txt")
    assert factory.is_file_exists_in_db(test_user, "file2.txt")
    assert factory.is_file_exists_in_minio(test_user, "file1.txt")
    assert factory.is_file_exists_in_minio(test_user, "file2.txt")
    assert File.objects.filter(user=test_user).count() == 2
