import json

from storage.models import File, Folder
from storage.services.minio_service import MinioService


def get_minio_service():
    return MinioService()


def upload_file(auth_client, file, path=""):
    if path:
        if path.endswith("/"):
            file_path = f"{path}{file.name}"
        else:
            file_path = f"{path}/{file.name}"
    else:
        file_path = file.name

    response = auth_client.post(
        "/api/resource",
        {
            "object": [file],
            "paths": json.dumps([file_path]),
        },
        format="multipart",
    )
    assert response.status_code == 201
    return response


def create_folder(auth_client, test_user, folder_path):
    auth_client.post(f"/api/directory?path={folder_path}", format="json")

    folder = Folder.objects.get(user=test_user, full_path=folder_path)
    return folder


def is_file_exists_in_minio(test_user, full_path):
    minio = get_minio_service()
    try:
        return minio.is_file_exists(test_user.id, full_path)
    except Exception as e:
        print(f"Error in is_file_exists_in_minio: {e}")
        return False


def is_file_exists_in_db(test_user, full_path):
    return File.objects.filter(user=test_user, full_path=full_path).exists()


def assert_file_response_data(data, path, name):
    assert data["path"] == path
    assert data["name"] == name
    assert "size" in data
    assert data["type"] == "FILE"


def assert_folder_response_data(data, path, name):
    assert data["path"] == path
    assert data["name"] == name
    assert "size" not in data
    assert data["type"] == "DIRECTORY"
