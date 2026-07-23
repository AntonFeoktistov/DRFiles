import json


def upload_file(auth_client, file, path=""):
    full_path = path + file.name
    data = {
        "object": [file],
        "paths": json.dumps([full_path]),
    }

    response = auth_client.post(
        "/api/resource",
        data,
        format="multipart",
    )
    assert response.status_code == 201
    return response


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
