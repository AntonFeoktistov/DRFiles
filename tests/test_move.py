import pytest
from django.contrib.auth import get_user_model

from storage.models import Folder
from tests import factory
from tests.conftest import make_auth_client_2

User = get_user_model()
pytestmark = pytest.mark.django_db


# ==================== ТЕСТЫ ПЕРЕМЕЩЕНИЯ ФАЙЛОВ ====================


def test_move_file_success(auth_client, test_user, make_test_file):
    file = make_test_file(name="file.txt", content="Content")
    factory.upload_file(auth_client, file)
    folder = factory.create_folder(auth_client, test_user, "target/")

    assert factory.is_file_exists_in_db(test_user, "file.txt")
    assert factory.is_file_exists_in_minio(test_user, "file.txt")

    response = auth_client.post(
        "/api/resource/move?from=file.txt&to=target/file.txt",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    factory.assert_file_response_data(data, folder.full_path, file.name)

    assert not factory.is_file_exists_in_db(test_user, "file.txt")
    assert not factory.is_file_exists_in_minio(test_user, "file.txt")
    assert factory.is_file_exists_in_db(test_user, "target/file.txt")
    assert factory.is_file_exists_in_minio(test_user, "target/file.txt")


def test_rename_file_success(auth_client, test_user, make_test_file):
    file = make_test_file(name="old_name.txt", content="Content")
    factory.upload_file(auth_client, file)

    assert factory.is_file_exists_in_db(test_user, "old_name.txt")
    assert factory.is_file_exists_in_minio(test_user, "old_name.txt")

    response = auth_client.post(
        "/api/resource/move?from=old_name.txt&to=new_name.txt",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    factory.assert_file_response_data(data, "", "new_name.txt")

    assert not factory.is_file_exists_in_db(test_user, "old_name.txt")
    assert not factory.is_file_exists_in_minio(test_user, "old_name.txt")

    assert factory.is_file_exists_in_db(test_user, "new_name.txt")
    assert factory.is_file_exists_in_minio(test_user, "new_name.txt")


def test_move_file_to_existing_path(auth_client, test_user, make_test_file):
    file1 = make_test_file(name="file1.txt", content="Content 1")
    file2 = make_test_file(name="file2.txt", content="Content 2")
    factory.upload_file(auth_client, file1)
    factory.upload_file(auth_client, file2)

    response = auth_client.post(
        "/api/resource/move?from=file1.txt&to=file2.txt",
        format="json",
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_move_file_not_found(auth_client, test_user):
    response = auth_client.post(
        "/api/resource/move?from=not_exists.txt&to=target.txt",
        format="json",
    )
    assert response.status_code == 404


def test_move_file_parent_folder_not_exists(auth_client, test_user, make_test_file):
    file = make_test_file(name="file.txt", content="Content")
    factory.upload_file(auth_client, file)

    response = auth_client.post(
        "/api/resource/move?from=file.txt&to=not_exists/file.txt",
        format="json",
    )
    assert response.status_code == 404
    assert "Parent folder" in response.json()["detail"]


def test_move_file_not_auth(client, test_user):
    response = client.post(
        "/api/resource/move?from=file.txt&to=target/file.txt",
        format="json",
    )
    assert response.status_code == 401


def test_move_file_another_user(
    auth_client, test_user, test_user_2, client, make_test_file
):
    file = make_test_file(name="file.txt", content="Content")
    factory.upload_file(auth_client, file)

    auth_client_2 = make_auth_client_2(client, test_user_2)
    response = auth_client_2.post(
        "/api/resource/move?from=file.txt&to=new_file.txt",
        format="json",
    )
    assert response.status_code == 404


def test_move_file_invalid_from_path(auth_client, test_user):
    response = auth_client.post(
        "/api/resource/move?from=&to=target.txt",
        format="json",
    )
    assert response.status_code == 400


def test_move_file_invalid_to_path(auth_client, test_user, make_test_file):
    file = make_test_file(name="file.txt", content="Content")
    factory.upload_file(auth_client, file)

    response = auth_client.post(
        "/api/resource/move?from=file.txt&to=",
        format="json",
    )
    assert response.status_code == 400


def test_move_file_different_types(auth_client, test_user, make_test_file):
    file = make_test_file(name="file.txt", content="Content")
    factory.upload_file(auth_client, file)

    response = auth_client.post(
        "/api/resource/move?from=file.txt&to=target/",
        format="json",
    )
    assert response.status_code == 400


def test_move_file_with_spaces(auth_client, test_user, make_test_file):
    file = make_test_file(name="my file.txt", content="Content")
    factory.upload_file(auth_client, file)

    import urllib.parse

    from_path = urllib.parse.quote("my file.txt")
    to_path = urllib.parse.quote("my new file.txt")

    response = auth_client.post(
        f"/api/resource/move?from={from_path}&to={to_path}",
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["name"] == "my new file.txt"

    assert not factory.is_file_exists_in_db(test_user, "my file.txt")
    assert not factory.is_file_exists_in_minio(test_user, "my file.txt")

    assert factory.is_file_exists_in_db(test_user, "my new file.txt")
    assert factory.is_file_exists_in_minio(test_user, "my new file.txt")


def test_move_file_with_cyrillic(auth_client, test_user, make_test_file):
    file = make_test_file(name="файл.txt", content="Content")
    factory.upload_file(auth_client, file)

    import urllib.parse

    from_path = urllib.parse.quote("файл.txt")
    to_path = urllib.parse.quote("новый_файл.txt")

    response = auth_client.post(
        f"/api/resource/move?from={from_path}&to={to_path}",
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["name"] == "новый_файл.txt"

    assert not factory.is_file_exists_in_db(test_user, "файл.txt")
    assert not factory.is_file_exists_in_minio(test_user, "файл.txt")

    assert factory.is_file_exists_in_db(test_user, "новый_файл.txt")
    assert factory.is_file_exists_in_minio(test_user, "новый_файл.txt")


# ==================== ТЕСТЫ ПЕРЕМЕЩЕНИЯ ПАПОК ====================


def test_move_folder_success(auth_client, test_user):
    folder = factory.create_folder(auth_client, test_user, "source/")
    target = factory.create_folder(auth_client, test_user, "target/")

    response = auth_client.post(
        "/api/resource/move?from=source/&to=target/source/",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    factory.assert_folder_response_data(data, target.full_path, folder.name)
    assert not Folder.objects.filter(user=test_user, full_path="source/").exists()
    assert Folder.objects.filter(user=test_user, full_path="target/source/").exists()


def test_rename_folder_success(auth_client, test_user):
    folder = factory.create_folder(auth_client, test_user, "old_name/")

    response = auth_client.post(
        "/api/resource/move?from=old_name/&to=new_name/",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    factory.assert_folder_response_data(data, "", "new_name")
    assert not Folder.objects.filter(user=test_user, full_path="old_name/").exists()
    assert Folder.objects.filter(user=test_user, full_path="new_name/").exists()


def test_move_folder_with_files(auth_client, test_user, make_test_file):
    source = factory.create_folder(auth_client, test_user, "source/")

    file1 = make_test_file(name="file1.txt", content="Content 1")
    file2 = make_test_file(name="file2.txt", content="Content 2")
    factory.upload_file(auth_client, file1, path="source/")
    factory.upload_file(auth_client, file2, path="source/")

    assert factory.is_file_exists_in_db(test_user, "source/file1.txt")
    assert factory.is_file_exists_in_db(test_user, "source/file2.txt")
    assert factory.is_file_exists_in_minio(test_user, "source/file1.txt")
    assert factory.is_file_exists_in_minio(test_user, "source/file2.txt")

    target = factory.create_folder(auth_client, test_user, "target/")

    response = auth_client.post(
        "/api/resource/move?from=source/&to=target/source/",
        format="json",
    )
    assert response.status_code == 200

    assert Folder.objects.filter(user=test_user, full_path="target/source/").exists()

    assert factory.is_file_exists_in_db(test_user, "target/source/file1.txt")
    assert factory.is_file_exists_in_db(test_user, "target/source/file2.txt")
    assert factory.is_file_exists_in_minio(test_user, "target/source/file1.txt")
    assert factory.is_file_exists_in_minio(test_user, "target/source/file2.txt")

    assert not factory.is_file_exists_in_db(test_user, "source/file1.txt")
    assert not factory.is_file_exists_in_db(test_user, "source/file2.txt")
    assert not factory.is_file_exists_in_minio(test_user, "source/file1.txt")
    assert not factory.is_file_exists_in_minio(test_user, "source/file2.txt")


def test_move_nested_folder(auth_client, test_user, make_test_file):
    parent = factory.create_folder(auth_client, test_user, "parent/")
    child = factory.create_folder(auth_client, test_user, "parent/child/")

    file = make_test_file(name="file.txt", content="Content")
    factory.upload_file(auth_client, file, path="parent/child/")

    assert factory.is_file_exists_in_db(test_user, "parent/child/file.txt")
    assert factory.is_file_exists_in_minio(test_user, "parent/child/file.txt")

    target = factory.create_folder(auth_client, test_user, "target/")
    response = auth_client.post(
        "/api/resource/move?from=parent/child/&to=target/child/",
        format="json",
    )
    assert response.status_code == 200

    assert not Folder.objects.filter(user=test_user, full_path="parent/child/").exists()
    assert Folder.objects.filter(user=test_user, full_path="target/child/").exists()

    assert factory.is_file_exists_in_db(test_user, "target/child/file.txt")
    assert factory.is_file_exists_in_minio(test_user, "target/child/file.txt")
    assert not factory.is_file_exists_in_db(test_user, "parent/child/file.txt")
    assert not factory.is_file_exists_in_minio(test_user, "parent/child/file.txt")


def test_move_folder_to_existing_path(auth_client, test_user):
    folder1 = factory.create_folder(auth_client, test_user, "folder1/")
    folder2 = factory.create_folder(auth_client, test_user, "folder2/")
    response = auth_client.post(
        "/api/resource/move?from=folder1/&to=folder2/",
        format="json",
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_move_folder_not_found(auth_client, test_user):
    response = auth_client.post(
        "/api/resource/move?from=not_exists/&to=target/",
        format="json",
    )
    assert response.status_code == 404


def test_move_folder_parent_not_exists(auth_client, test_user):
    folder = factory.create_folder(auth_client, test_user, "source/")
    response = auth_client.post(
        "/api/resource/move?from=source/&to=not_exists/source/",
        format="json",
    )
    assert response.status_code == 404
    assert "Parent folder" in response.json()["detail"]


def test_move_folder_not_auth(client, test_user):
    response = client.post(
        "/api/resource/move?from=folder/&to=target/folder/",
        format="json",
    )
    assert response.status_code == 401


def test_move_folder_another_user(auth_client, test_user, test_user_2, client):
    folder = factory.create_folder(auth_client, test_user, "source/")

    auth_client_2 = make_auth_client_2(client, test_user_2)
    response = auth_client_2.post(
        "/api/resource/move?from=source/&to=new_source/",
        format="json",
    )
    assert response.status_code == 404


def test_move_folder_different_types(auth_client, test_user, make_test_file):
    folder = factory.create_folder(auth_client, test_user, "source/")
    file = make_test_file(name="file.txt", content="Content")
    factory.upload_file(auth_client, file)

    response = auth_client.post(
        "/api/resource/move?from=source/&to=file.txt",
        format="json",
    )
    assert response.status_code == 400


def test_move_folder_with_subfolders(auth_client, test_user, make_test_file):
    root = factory.create_folder(auth_client, test_user, "root/")
    sub1 = factory.create_folder(auth_client, test_user, "root/sub1/")
    sub2 = factory.create_folder(auth_client, test_user, "root/sub1/sub2/")

    file = make_test_file(name="file.txt", content="Content")
    factory.upload_file(auth_client, file, path="root/sub1/sub2/")

    assert factory.is_file_exists_in_db(test_user, "root/sub1/sub2/file.txt")
    assert factory.is_file_exists_in_minio(test_user, "root/sub1/sub2/file.txt")

    target = factory.create_folder(auth_client, test_user, "target/")

    response = auth_client.post(
        "/api/resource/move?from=root/sub1/&to=target/sub1/",
        format="json",
    )
    assert response.status_code == 200

    assert not Folder.objects.filter(user=test_user, full_path="root/sub1/").exists()
    assert Folder.objects.filter(user=test_user, full_path="target/sub1/").exists()
    assert Folder.objects.filter(user=test_user, full_path="target/sub1/sub2/").exists()

    assert factory.is_file_exists_in_db(test_user, "target/sub1/sub2/file.txt")
    assert factory.is_file_exists_in_minio(test_user, "target/sub1/sub2/file.txt")
    assert not factory.is_file_exists_in_db(test_user, "root/sub1/sub2/file.txt")
    assert not factory.is_file_exists_in_minio(test_user, "root/sub1/sub2/file.txt")


def test_move_root_folder(auth_client, test_user):
    folder = factory.create_folder(auth_client, test_user, "source/")
    auth_client.post(f"/api/directory?path={folder.full_path}", format="json")

    response = auth_client.post(
        "/api/resource/move?from=source/&to=",
        format="json",
    )
    assert response.status_code == 409


def test_move_file_to_root(auth_client, test_user, make_test_file):
    folder = factory.create_folder(auth_client, test_user, "source/")
    file = make_test_file(name="file.txt", content="Content")
    factory.upload_file(auth_client, file, path="source/")

    assert factory.is_file_exists_in_db(test_user, "source/file.txt")
    assert factory.is_file_exists_in_minio(test_user, "source/file.txt")

    response = auth_client.post(
        "/api/resource/move?from=source/file.txt&to=file.txt",
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["path"] == ""
    assert response.json()["name"] == "file.txt"

    assert factory.is_file_exists_in_db(test_user, "file.txt")
    assert factory.is_file_exists_in_minio(test_user, "file.txt")
    assert not factory.is_file_exists_in_db(test_user, "source/file.txt")
    assert not factory.is_file_exists_in_minio(test_user, "source/file.txt")
