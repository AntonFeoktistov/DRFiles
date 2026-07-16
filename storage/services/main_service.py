from typing import Any, List, Optional

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from rest_framework.exceptions import NotFound, ParseError

from config.exceptions import ConflictError
from storage.models import Folder
from storage.serializers import ResourceResponseSerializer
from storage.services import path_utils
from storage.services.delete_service import DeleteService
from storage.services.download_service import DownloadService
from storage.services.minio_service import get_minio_service
from storage.services.move_service import MoveService
from storage.services.repository import StorageRepository


class StorageService:
    def __init__(self):
        self.minio = get_minio_service()
        self.repo = StorageRepository()
        self.delete = DeleteService(self.minio, self.repo)
        self.download = DownloadService(self.minio, self.repo)
        self.move = MoveService(self.minio, self.repo)

    def get_resource(self, user_id: int, path: str):
        if path_utils.is_resource_folder(path):
            resource = self.repo.get_folder_or_none(user_id, path)
        else:
            resource = self.repo.get_file_or_none(user_id, path)
        return resource

    def delete_resource(self, user_id: int, path: str):
        if path_utils.is_resource_folder(path):
            self.delete.delete_folder(user_id, path)
        else:
            self.delete.delete_file(user_id, path)

    def download_resource(self, user_id: int, path: str):
        if path_utils.is_resource_folder(path):
            return self.download.download_folder(user_id, path)
        else:
            return self.download.download_file(user_id, path)

    def move_resource(self, user_id: int, path_from: str, path_to: str):
        if path_utils.is_resource_folder(path_from):
            return self.move.move_folder(user_id, path_from, path_to)
        else:
            return self.move.move_file(user_id, path_from, path_to)

    def create_directory(self, user_id: int, folder_path: str):
        if not path_utils.is_resource_folder(folder_path):
            raise ParseError(f"{folder_path} is not valid folder path")
        existing = self.repo.get_folder_or_none(user_id, folder_path)
        if existing:
            raise ConflictError(f"Folder {folder_path} is already exsists")

        folder_name, parent_path = path_utils.get_name_and_parent_path(folder_path)

        parent = self.repo.get_folder_or_none(user_id, parent_path)
        if not parent:
            raise NotFound(f"Parent folder not found: {parent_path}")
        folder = self.repo.create_folder(user_id, folder_path)
        return folder

    def search_resources(self, user_id: int, query: str):
        files = self.repo.get_files_by_query(user_id, query)
        folders = self.repo.get_folders_by_query(user_id, query)
        return files + folders

    @transaction.atomic
    def upload_files(
        self, user_id: int, path: str, files: List[UploadedFile]
    ) -> List[dict[str, Any]]:
        if not files:
            return []

        folder = self.repo.get_folder_or_none(user_id, path)
        if not folder:
            raise NotFound(f"Folder '{path}' not found")

        uploaded_resources = []

        for file in files:
            file_name, parent_path = path_utils.get_name_and_parent_path(file.name)

            full_file_path = path_utils.join_paths(path, parent_path, file_name)

            if self.repo.get_file_or_none(user_id, full_file_path):
                raise ConflictError(f"File '{full_file_path}' already exists")

            if self.minio.is_file_exists(user_id, full_file_path):
                raise ConflictError(
                    f"File '{full_file_path}' already exists in storage"
                )

            if parent_path:
                target_folder = self._ensure_folder_path(
                    user_id, path_utils.join_paths(path, parent_path)
                )
            else:
                target_folder = folder

            self.minio.upload_file(
                user_id, full_file_path, file, content_type=file.content_type
            )

            db_file = self.repo.create_file_in_db(
                user_id=user_id,
                folder_id=target_folder.id,
                full_path=full_file_path,
                file_size=file.size,
            )

            serializer = ResourceResponseSerializer(db_file)
            uploaded_resources.append(serializer.data)

        return uploaded_resources

    def upload_single_file(
        self, user_id: int, path: str, file: UploadedFile
    ) -> Optional[dict[str, Any]]:
        result = self.upload_files(user_id, path, [file])
        return result[0] if result else None

    def _ensure_folder_path(self, user_id: int, path: str) -> Folder:
        if not path:
            return None

        folder = self.repo.get_folder_or_none(user_id, path)
        if folder:
            return folder

        parts = path.split("/")
        current_path = ""
        parent = None

        for part in parts:
            if not part:
                continue
            current_path = f"{current_path}/{part}".strip("/") if current_path else part
            folder = self.repo.get_folder_or_none(user_id, current_path)
            if not folder:
                folder = self.repo.create_folder(user_id, current_path, parent)
            parent = folder

        return folder
