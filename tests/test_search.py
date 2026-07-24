import pytest
from django.contrib.auth import get_user_model

from tests import factory
from tests.conftest import make_auth_client_2

User = get_user_model()
pytestmark = pytest.mark.django_db


# ==================== ТЕСТЫ ПОИСКА ====================


def test_search_files_by_name(auth_client, test_user, make_test_file):
    file1 = make_test_file(name="document.pdf", content=b"PDF")
    file2 = make_test_file(name="report.doc", content=b"DOC")
    file3 = make_test_file(name="image.png", content=b"PNG")
    factory.upload_file(auth_client, file1)
    factory.upload_file(auth_client, file2)
    factory.upload_file(auth_client, file3)

    response = auth_client.get(
        "/api/resource/search?query=doc",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2

    names = [item["name"] for item in data]
    assert "document.pdf" in names
    assert "report.doc" in names
    assert "image.png" not in names


def test_search_folders_by_name(auth_client, test_user):
    folder1 = factory.create_folder(auth_client, test_user, "documents/")
    folder2 = factory.create_folder(auth_client, test_user, "images/")
    folder3 = factory.create_folder(auth_client, test_user, "videos/")
    auth_client.post(f"/api/directory?path={folder1.full_path}", format="json")
    auth_client.post(f"/api/directory?path={folder2.full_path}", format="json")
    auth_client.post(f"/api/directory?path={folder3.full_path}", format="json")

    response = auth_client.get(
        "/api/resource/search?query=doc",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "documents"
    assert data[0]["type"] == "DIRECTORY"


def test_search_files_in_folder(auth_client, test_user, make_test_file):
    folder = factory.create_folder(auth_client, test_user, "documents/")

    file1 = make_test_file(name="report.pdf", content=b"PDF")
    file2 = make_test_file(name="image.png", content=b"PNG")
    file3 = make_test_file(name="data.csv", content=b"CSV")
    factory.upload_file(auth_client, file1, path="documents/")
    factory.upload_file(auth_client, file2, path="documents/")
    factory.upload_file(auth_client, file3)

    response = auth_client.get(
        "/api/resource/search?query=report",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["path"] == "documents/"
    assert data[0]["name"] == "report.pdf"
    assert data[0]["type"] == "FILE"


def test_search_case_insensitive(auth_client, test_user, make_test_file):
    file1 = make_test_file(name="Document.pdf", content=b"PDF")
    file2 = make_test_file(name="document.pdf", content=b"PDF")
    factory.upload_file(auth_client, file1)
    factory.upload_file(auth_client, file2)

    response = auth_client.get(
        "/api/resource/search?query=DOCUMENT",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2


def test_search_partial_match(auth_client, test_user, make_test_file):
    file1 = make_test_file(name="document.pdf", content=b"PDF")
    file2 = make_test_file(name="report.doc", content=b"DOC")
    factory.upload_file(auth_client, file1)
    factory.upload_file(auth_client, file2)

    response = auth_client.get(
        "/api/resource/search?query=docu",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "document.pdf"


def test_search_empty_query(auth_client, test_user):
    response = auth_client.get(
        "/api/resource/search?query=",
        format="json",
    )
    assert response.status_code == 400


def test_search_no_query(auth_client, test_user):
    response = auth_client.get(
        "/api/resource/search",
        format="json",
    )
    assert response.status_code == 400


def test_search_no_results(auth_client, test_user, make_test_file):
    file = make_test_file(name="document.pdf", content=b"PDF")
    factory.upload_file(auth_client, file)

    response = auth_client.get(
        "/api/resource/search?query=notexists",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 0


def test_search_not_auth(client, test_user):
    response = client.get(
        "/api/resource/search?query=test",
        format="json",
    )
    assert response.status_code == 401


def test_search_files_and_folders(auth_client, test_user, make_test_file):
    folder = factory.create_folder(auth_client, test_user, "documents/")
    auth_client.post(f"/api/directory?path={folder.full_path}", format="json")

    file1 = make_test_file(name="document.pdf", content=b"PDF")
    file2 = make_test_file(name="doc.txt", content=b"TXT")
    factory.upload_file(auth_client, file1)
    factory.upload_file(auth_client, file2)

    response = auth_client.get(
        "/api/resource/search?query=doc",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 3

    types = [item["type"] for item in data]
    assert "FILE" in types
    assert "DIRECTORY" in types


def test_search_another_user(
    auth_client, test_user, test_user_2, client, make_test_file
):
    file1 = make_test_file(name="document.pdf", content=b"PDF")
    factory.upload_file(auth_client, file1)

    auth_client_2 = make_auth_client_2(client, test_user_2)
    file2 = make_test_file(name="document.pdf", content=b"PDF")
    factory.upload_file(auth_client_2, file2)

    response = auth_client.get(
        "/api/resource/search?query=document",
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    response = auth_client_2.get(
        "/api/resource/search?query=document",
        format="json",
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_search_with_spaces(auth_client, test_user, make_test_file):
    file1 = make_test_file(name="my document.pdf", content=b"PDF")
    file2 = make_test_file(name="your document.pdf", content=b"PDF")
    factory.upload_file(auth_client, file1)
    factory.upload_file(auth_client, file2)

    import urllib.parse

    query = urllib.parse.quote("my document")
    response = auth_client.get(
        f"/api/resource/search?query={query}",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "my document.pdf"


def test_search_with_cyrillic(auth_client, test_user, make_test_file):
    file1 = make_test_file(name="документ.pdf", content=b"PDF")
    file2 = make_test_file(name="отчёт.doc", content=b"DOC")
    factory.upload_file(auth_client, file1)
    factory.upload_file(auth_client, file2)

    import urllib.parse

    query = urllib.parse.quote("документ")
    response = auth_client.get(
        f"/api/resource/search?query={query}",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "документ.pdf"


def test_search_special_characters(auth_client, test_user, make_test_file):
    file = make_test_file(name="file (1).pdf", content=b"PDF")
    factory.upload_file(auth_client, file)

    import urllib.parse

    query = urllib.parse.quote("file (1)")
    response = auth_client.get(
        f"/api/resource/search?query={query}",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "file (1).pdf"


def test_search_response_format(auth_client, test_user, make_test_file):
    file = make_test_file(name="test.txt", content="Content")
    factory.upload_file(auth_client, file)

    response = auth_client.get(
        "/api/resource/search?query=test",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    item = data[0]
    assert "path" in item
    assert "name" in item
    assert "size" in item
    assert "type" in item
    assert item["type"] == "FILE"


def test_search_folder_response_format(auth_client, test_user):
    folder = factory.create_folder(auth_client, test_user, "testfolder/")

    response = auth_client.get(
        "/api/resource/search?query=testfolder",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1

    item = data[0]
    assert "path" in item
    assert "name" in item
    assert "size" not in item
    assert item["type"] == "DIRECTORY"


def test_search_long_query(auth_client, test_user, make_test_file):
    file = make_test_file(
        name="very_long_filename_with_many_characters.txt", content=b"Content"
    )
    factory.upload_file(auth_client, file)

    response = auth_client.get(
        "/api/resource/search?query=very_long_filename",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "very_long_filename_with_many_characters.txt"


def test_search_nested_structure(auth_client, test_user, make_test_file):
    parent = factory.create_folder(auth_client, test_user, "parent/")
    child = factory.create_folder(auth_client, test_user, "parent/child/")
    grandchild = factory.create_folder(
        auth_client, test_user, "parent/child/grandchild/"
    )

    file = make_test_file(name="file.txt", content="Content")
    factory.upload_file(auth_client, file, path="parent/child/grandchild/")

    response = auth_client.get(
        "/api/resource/search?query=file",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["path"] == "parent/child/grandchild/"
    assert data[0]["name"] == "file.txt"


def test_search_with_numbers(auth_client, test_user, make_test_file):
    file1 = make_test_file(name="file123.txt", content=b"Content")
    file2 = make_test_file(name="file456.txt", content=b"Content")
    factory.upload_file(auth_client, file1)
    factory.upload_file(auth_client, file2)

    response = auth_client.get(
        "/api/resource/search?query=123",
        format="json",
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "file123.txt"
