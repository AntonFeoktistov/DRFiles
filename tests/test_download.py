import zipfile
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model

from tests import factory
from tests.conftest import make_auth_client_2

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_download_file_success(auth_client, test_user, make_test_file):
    file = make_test_file(name="test1.txt", content="Hello World")
    factory.upload_file(auth_client, file)

    response = auth_client.get(
        "/api/resource/download?path=test1.txt",
    )
    assert response.status_code == 200
    content = b"".join(response.streaming_content)
    assert content == b"Hello World"
    assert response.headers["content-type"] == "application/octet-stream"
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "test1.txt" in response.headers.get("content-disposition", "")


def test_download_file_not_found(auth_client, test_user, make_test_file):
    file = make_test_file(name="test1.txt")
    factory.upload_file(auth_client, file)

    response = auth_client.get(
        "/api/resource/download?path=NOT_EXISTS.txt",
    )
    assert response.status_code == 404


def test_download_file_not_auth(client, test_user, make_test_file):
    file = make_test_file(name="test1.txt")

    response = client.get(
        "/api/resource/download?path=test1.txt",
    )
    assert response.status_code == 401


def test_download_file_another_user(
    auth_client, test_user, test_user_2, client, make_test_file
):
    file = make_test_file(name="test1.txt")
    factory.upload_file(auth_client, file)

    auth_client_2 = make_auth_client_2(client, test_user_2)

    response = auth_client_2.get(
        "/api/resource/download?path=test1.txt",
    )
    assert response.status_code == 404


def test_download_file_with_path(auth_client, test_user, make_test_file):
    file = make_test_file(name="report.pdf", content=b"PDF content")
    factory.upload_file(auth_client, file, path="documents/")

    response = auth_client.get(
        "/api/resource/download?path=documents/report.pdf",
    )
    assert response.status_code == 200
    content = b"".join(response.streaming_content)
    assert content == b"PDF content"
    assert "report.pdf" in response.headers.get("content-disposition", "")


def test_download_file_with_spaces(auth_client, test_user, make_test_file):
    file = make_test_file(name="my report.pdf", content=b"PDF content")
    factory.upload_file(auth_client, file)

    response = auth_client.get(
        "/api/resource/download?path=my%20report.pdf",
    )
    assert response.status_code == 200
    content = b"".join(response.streaming_content)
    assert content == b"PDF content"
    content_disposition = response.headers.get("content-disposition", "")
    assert (
        "my report.pdf" in content_disposition
        or "my%20report.pdf" in content_disposition
    )


def test_download_file_with_cyrillic(auth_client, test_user, make_test_file):
    file = make_test_file(name="отчёт.pdf", content=b"PDF content")
    factory.upload_file(auth_client, file)

    import urllib.parse

    encoded_path = urllib.parse.quote("отчёт.pdf")
    response = auth_client.get(
        f"/api/resource/download?path={encoded_path}",
    )
    assert response.status_code == 200
    content = b"".join(response.streaming_content)
    assert content == b"PDF content"


def test_download_folder_success(auth_client, test_user, make_test_file):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")

    file1 = make_test_file(name="test1.txt", content="Content 1")
    file2 = make_test_file(name="test2.txt", content="Content 2")
    factory.upload_file(auth_client, file1, path="testfolder/")
    factory.upload_file(auth_client, file2, path="testfolder/")

    response = auth_client.get(
        f"/api/resource/download?path={folder.full_path}",
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    zip_content = BytesIO(b"".join(response.streaming_content))
    with zipfile.ZipFile(zip_content, "r") as zip_file:
        zip_names = zip_file.namelist()
        assert len(zip_names) == 2
        assert "testfolder/test1.txt" in zip_names
        assert "testfolder/test2.txt" in zip_names
        assert zip_file.read("testfolder/test1.txt").decode("utf-8") == "Content 1"
        assert zip_file.read("testfolder/test2.txt").decode("utf-8") == "Content 2"


def test_download_folder_with_subfolders(auth_client, test_user, make_test_file):
    root = factory.create_folder(auth_client, test_user, "testfolder/")
    src = factory.create_folder(auth_client, test_user, "testfolder/src/")
    factory.create_folder(auth_client, test_user, "testfolder/src/utils/")

    file1 = make_test_file(name="main.py", content=b"print('Hello')")
    file2 = make_test_file(name="helpers.py", content=b"def help(): pass")
    factory.upload_file(auth_client, file1, path="testfolder/src/")
    factory.upload_file(auth_client, file2, path="testfolder/src/utils/")

    response = auth_client.get(
        "/api/resource/download?path=testfolder/",
    )
    assert response.status_code == 200

    zip_content = BytesIO(b"".join(response.streaming_content))
    with zipfile.ZipFile(zip_content, "r") as zip_file:
        zip_names = zip_file.namelist()
        assert "testfolder/src/main.py" in zip_names
        assert "testfolder/src/utils/helpers.py" in zip_names


def test_download_empty_folder(auth_client, test_user):
    folder = factory.create_folder(auth_client, test_user, "empty/")

    response = auth_client.get(
        f"/api/resource/download?path={folder.full_path}",
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    zip_content = BytesIO(b"".join(response.streaming_content))
    with zipfile.ZipFile(zip_content, "r") as zip_file:
        assert len(zip_file.namelist()) == 0


def test_download_root_folder(auth_client, test_user, make_test_file):
    file1 = make_test_file(name="file1.txt", content=b"Content 1")
    file2 = make_test_file(name="file2.txt", content=b"Content 2")
    factory.upload_file(auth_client, file1)
    factory.upload_file(auth_client, file2)

    folder = factory.create_folder(auth_client, test_user, "docs/")
    file3 = make_test_file(name="doc.txt", content=b"Doc content")
    factory.upload_file(auth_client, file3, path="docs/")

    response = auth_client.get(
        "/api/resource/download?path=",
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    zip_content = BytesIO(b"".join(response.streaming_content))
    with zipfile.ZipFile(zip_content, "r") as zip_file:
        zip_names = zip_file.namelist()
        assert "file1.txt" in zip_names
        assert "file2.txt" in zip_names
        assert "docs/doc.txt" in zip_names
        assert len(zip_names) == 3


def test_download_folder_not_exists(auth_client, test_user):
    response = auth_client.get(
        "/api/resource/download?path=notexists/",
    )
    assert response.status_code == 404


def test_download_folder_not_auth(client, test_user):
    response = client.get(
        "/api/resource/download?path=testfolder/",
    )
    assert response.status_code == 401


def test_download_folder_another_user(
    auth_client, test_user, test_user_2, client, make_test_file
):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")
    file = make_test_file(name="test.txt", content=b"Secret")
    factory.upload_file(auth_client, file, path="testfolder/")

    auth_client_2 = make_auth_client_2(client, test_user_2)

    response = auth_client_2.get(
        f"/api/resource/download?path={folder.full_path}",
    )
    assert response.status_code == 404
