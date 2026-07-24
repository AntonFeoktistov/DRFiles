import json

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from storage.models import File, Folder
from tests import factory

User = get_user_model()
pytestmark = pytest.mark.django_db


# ==================== ТЕСТЫ ЗАГРУЗКИ ФАЙЛОВ ====================


def test_upload_file_success(auth_client, test_user, make_test_file):
    file = make_test_file()

    response = auth_client.post(
        "/api/resource",
        {
            "object": [file],
            "paths": json.dumps([file.name]),
        },
        format="multipart",
    )
    assert response.status_code == 201

    data = response.json()[0]
    assert data["path"] == ""
    assert data["name"] == file.name
    assert "size" in data
    assert data["type"] == "FILE"

    assert factory.is_file_exists_in_db(test_user, file.name)
    assert factory.is_file_exists_in_minio(test_user, file.name)


def test_upload_file_duplicate(auth_client, test_user, make_test_file):
    file = make_test_file()

    response = auth_client.post(
        "/api/resource",
        {
            "object": [file],
            "paths": json.dumps([file.name]),
        },
        format="multipart",
    )
    assert response.status_code == 201

    assert factory.is_file_exists_in_db(test_user, file.name)
    assert factory.is_file_exists_in_minio(test_user, file.name)

    response = auth_client.post(
        "/api/resource",
        {
            "object": [file],
            "paths": json.dumps([file.name]),
        },
        format="multipart",
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_upload_file_not_auth(client, test_user, make_test_file):
    file = make_test_file()

    response = client.post(
        "/api/resource",
        {
            "object": [file],
            "paths": json.dumps([file.name]),
        },
        format="multipart",
    )
    assert response.status_code == 401


def test_upload_file_no_file(auth_client, test_user):
    response = auth_client.post(
        "/api/resource",
        {
            "object": [],
            "paths": json.dumps([]),
        },
        format="multipart",
    )
    assert response.status_code == 400


def test_upload_file_with_path(auth_client, test_user):
    file = SimpleUploadedFile(
        name="report.pdf",
        content=b"PDF content",
        content_type="application/pdf",
    )

    response = auth_client.post(
        "/api/resource?path=",
        {
            "object": [file],
            "paths": json.dumps(["documents/report.pdf"]),
        },
        format="multipart",
    )
    assert response.status_code == 201

    data = response.json()[0]
    assert data["path"] == "documents/"
    assert data["name"] == "report.pdf"

    assert factory.is_file_exists_in_db(test_user, "documents/report.pdf")
    assert factory.is_file_exists_in_minio(test_user, "documents/report.pdf")


def test_upload_multiple_files_with_paths(auth_client, test_user):
    files = [
        SimpleUploadedFile("readme.txt", b"# Project"),
        SimpleUploadedFile("main.py", b"print('Hello')"),
        SimpleUploadedFile("helpers.py", b"def help(): pass"),
        SimpleUploadedFile("test.py", b"def test(): pass"),
    ]

    paths = [
        "project/README.md",
        "project/src/main.py",
        "project/src/utils/helpers.py",
        "project/tests/test_main.py",
    ]

    response = auth_client.post(
        "/api/resource?path=",
        {
            "object": files,
            "paths": json.dumps(paths),
        },
        format="multipart",
    )
    assert response.status_code == 201

    folders = Folder.objects.filter(user=test_user)
    folder_paths = [f.full_path for f in folders]
    assert "project/" in folder_paths
    assert "project/src/" in folder_paths
    assert "project/src/utils/" in folder_paths
    assert "project/tests/" in folder_paths

    for path in paths:
        assert factory.is_file_exists_in_db(test_user, path)
        assert factory.is_file_exists_in_minio(test_user, path)


def test_upload_with_base_path(auth_client, test_user):
    factory.create_folder(auth_client, test_user, "documents/")

    files = [
        SimpleUploadedFile("report.pdf", b"PDF content"),
        SimpleUploadedFile("file.txt", b"Text content"),
    ]

    paths = [
        "report.pdf",
        "subfolder/file.txt",
    ]

    response = auth_client.post(
        "/api/resource?path=documents/",
        {
            "object": files,
            "paths": json.dumps(paths),
        },
        format="multipart",
    )
    assert response.status_code == 201

    assert factory.is_file_exists_in_db(test_user, "documents/report.pdf")
    assert factory.is_file_exists_in_minio(test_user, "documents/report.pdf")
    assert factory.is_file_exists_in_db(test_user, "documents/subfolder/file.txt")
    assert factory.is_file_exists_in_minio(test_user, "documents/subfolder/file.txt")


def test_upload_folder_with_structure(auth_client, test_user):
    files = [
        SimpleUploadedFile("README.md", b"# Project"),
        SimpleUploadedFile("main.py", b"print('Hello')"),
        SimpleUploadedFile("helpers.py", b"def help(): pass"),
        SimpleUploadedFile("test_main.py", b"def test(): pass"),
    ]

    paths = [
        "project/README.md",
        "project/src/main.py",
        "project/src/utils/helpers.py",
        "project/tests/test_main.py",
    ]

    response = auth_client.post(
        "/api/resource?path=",
        {
            "object": files,
            "paths": json.dumps(paths),
        },
        format="multipart",
    )
    assert response.status_code == 201

    data = response.json()
    assert len(data) == 4

    folders = Folder.objects.filter(user=test_user)
    folder_paths = [f.full_path for f in folders]
    assert "project/" in folder_paths
    assert "project/src/" in folder_paths
    assert "project/src/utils/" in folder_paths
    assert "project/tests/" in folder_paths

    files_in_db = File.objects.filter(user=test_user)
    assert len(files_in_db) == 4

    expected_paths = [
        "project/README.md",
        "project/src/main.py",
        "project/src/utils/helpers.py",
        "project/tests/test_main.py",
    ]

    for path in expected_paths:
        assert factory.is_file_exists_in_db(test_user, path)
        assert factory.is_file_exists_in_minio(test_user, path)


def test_upload_duplicate_file_with_path(auth_client, test_user):
    file = SimpleUploadedFile(
        name="report.pdf",
        content=b"PDF content",
    )

    response = auth_client.post(
        "/api/resource?path=",
        {
            "object": [file],
            "paths": json.dumps(["documents/report.pdf"]),
        },
        format="multipart",
    )
    assert response.status_code == 201

    assert factory.is_file_exists_in_db(test_user, "documents/report.pdf")
    assert factory.is_file_exists_in_minio(test_user, "documents/report.pdf")

    response = auth_client.post(
        "/api/resource?path=",
        {
            "object": [file],
            "paths": json.dumps(["documents/report.pdf"]),
        },
        format="multipart",
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_upload_nested_into_existing_folder(auth_client, test_user):
    factory.create_folder(auth_client, test_user, "backup/")

    files = [
        SimpleUploadedFile("report.pdf", b"PDF"),
        SimpleUploadedFile("data.csv", b"CSV"),
        SimpleUploadedFile("plan.md", b"Plan"),
    ]

    paths = [
        "backup/2024/report.pdf",
        "backup/2024/data.csv",
        "backup/2025/plan.md",
    ]

    response = auth_client.post(
        "/api/resource?path=",
        {
            "object": files,
            "paths": json.dumps(paths),
        },
        format="multipart",
    )
    assert response.status_code == 201

    expected = [
        "backup/2024/report.pdf",
        "backup/2024/data.csv",
        "backup/2025/plan.md",
    ]

    for path in expected:
        assert factory.is_file_exists_in_db(test_user, path)
        assert factory.is_file_exists_in_minio(test_user, path)


def test_upload_multiple_files_different_folders(auth_client, test_user):
    files = [
        SimpleUploadedFile("readme.txt", b"Docs"),
        SimpleUploadedFile("main.py", b"Code"),
        SimpleUploadedFile("utils.py", b"Utils"),
        SimpleUploadedFile("test.py", b"Tests"),
    ]

    paths = [
        "docs/readme.txt",
        "src/main.py",
        "src/utils.py",
        "tests/test.py",
    ]

    response = auth_client.post(
        "/api/resource?path=",
        {
            "object": files,
            "paths": json.dumps(paths),
        },
        format="multipart",
    )
    assert response.status_code == 201

    data = response.json()
    assert len(data) == 4

    expected = {
        "docs/readme.txt": "docs/",
        "src/main.py": "src/",
        "src/utils.py": "src/",
        "tests/test.py": "tests/",
    }

    for file_data in data:
        full_path = file_data["path"] + file_data["name"]
        assert full_path in expected
        assert factory.is_file_exists_in_db(test_user, full_path)
        assert factory.is_file_exists_in_minio(test_user, full_path)


def test_upload_deep_nested_structure(auth_client, test_user):
    files = [
        SimpleUploadedFile("file1.txt", b"1"),
        SimpleUploadedFile("file2.txt", b"2"),
        SimpleUploadedFile("file3.txt", b"3"),
    ]

    paths = [
        "a/b/c/d/file1.txt",
        "a/b/c/d/file2.txt",
        "a/b/e/file3.txt",
    ]

    response = auth_client.post(
        "/api/resource?path=",
        {
            "object": files,
            "paths": json.dumps(paths),
        },
        format="multipart",
    )
    assert response.status_code == 201

    expected_folders = [
        "a/",
        "a/b/",
        "a/b/c/",
        "a/b/c/d/",
        "a/b/e/",
    ]
    for folder_path in expected_folders:
        assert Folder.objects.filter(user=test_user, full_path=folder_path).exists()

    expected_files = [
        "a/b/c/d/file1.txt",
        "a/b/c/d/file2.txt",
        "a/b/e/file3.txt",
    ]

    for file_path in expected_files:
        assert factory.is_file_exists_in_db(test_user, file_path)
        assert factory.is_file_exists_in_minio(test_user, file_path)


def test_upload_file_with_spaces_in_path(auth_client, test_user):
    file = SimpleUploadedFile(
        name="report 2024.pdf",
        content=b"PDF",
    )

    response = auth_client.post(
        "/api/resource?path=",
        {
            "object": [file],
            "paths": json.dumps(["my documents/report 2024.pdf"]),
        },
        format="multipart",
    )
    assert response.status_code == 201

    data = response.json()[0]
    assert data["path"] == "my documents/"
    assert data["name"] == "report 2024.pdf"

    assert factory.is_file_exists_in_db(test_user, "my documents/report 2024.pdf")
    assert factory.is_file_exists_in_minio(test_user, "my documents/report 2024.pdf")


def test_upload_file_with_cyrillic_path(auth_client, test_user):
    file = SimpleUploadedFile(
        name="отчёт.pdf",
        content=b"PDF",
    )

    response = auth_client.post(
        "/api/resource?path=",
        {
            "object": [file],
            "paths": json.dumps(["документы/отчёт.pdf"]),
        },
        format="multipart",
    )
    assert response.status_code == 201

    data = response.json()[0]
    assert data["path"] == "документы/"
    assert data["name"] == "отчёт.pdf"

    assert factory.is_file_exists_in_db(test_user, "документы/отчёт.pdf")
    assert factory.is_file_exists_in_minio(test_user, "документы/отчёт.pdf")


# ==================== ТЕСТЫ СОЗДАНИЯ ПАПОК ====================


def test_create_folder_success(auth_client, test_user):
    full_path = "testfolder/"
    response = auth_client.post(
        f"/api/directory?path={full_path}",
        format="json",
    )

    assert response.status_code == 201

    data = response.json()
    assert data["path"] + data["name"] + "/" == full_path
    assert data["type"] == "DIRECTORY"

    assert Folder.objects.filter(user=test_user, full_path=full_path).exists()


def test_create_nested_folder_success(auth_client, test_user):
    auth_client.post("/api/directory?path=parent/", format="json")

    response = auth_client.post(
        "/api/directory?path=parent/child/",
        format="json",
    )
    assert response.status_code == 201

    data = response.json()
    assert data["path"] == "parent/"
    assert data["name"] == "child"
    assert data["type"] == "DIRECTORY"

    assert Folder.objects.filter(user=test_user, full_path="parent/child/").exists()


def test_create_folder_already_exists(auth_client, test_user):
    auth_client.post("/api/directory?path=exists/", format="json")

    response = auth_client.post(
        "/api/directory?path=exists/",
        format="json",
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()
