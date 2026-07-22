from typing import Any, List

from django.db import transaction

from config.exceptions import ConflictError
from storage.models import Folder
from storage.serializers import ResourceResponseSerializer
from storage.services.minio_service import MinioService
from storage.services.repository import StorageRepository


class UploadService:
    def __init__(self, minio_client: MinioService, repository: StorageRepository):
        self.minio = minio_client
        self.repo = repository

    @transaction.atomic
    def upload_files(
        self, user_id: int, base_path: str, files_with_paths: List[tuple]
    ) -> List[dict[str, Any]]:

        if not files_with_paths:
            return []

        base_path = self._normalize_path(base_path)
        root_folder = self._get_or_create_root_folder(user_id, base_path)

        uploaded_resources = []

        for file, file_path in files_with_paths:
            result = self._process_single_file(
                user_id, base_path, file, file_path, root_folder
            )
            uploaded_resources.append(result)

        return uploaded_resources

    def _normalize_path(self, path: str) -> str:
        return path.strip("/")

    def _get_or_create_root_folder(self, user_id: int, base_path: str) -> Folder:
        if base_path:
            root_folder = self.repo.get_folder_or_none(user_id, f"{base_path}/")
            if not root_folder:
                root_folder = self._ensure_folder_path(user_id, base_path)
        else:
            root_folder = self.repo.get_or_create_root_folder(user_id)

        return root_folder

    def _process_single_file(
        self, user_id: int, base_path: str, file, file_path: str, root_folder: Folder
    ) -> dict[str, Any]:

        parent_path, file_name = self._split_path_and_name(file_path)

        folder_full_path = self._build_folder_full_path(base_path, parent_path)
        target_folder = self._get_or_create_target_folder(
            user_id, folder_full_path, root_folder
        )
        full_file_path = self._build_file_full_path(folder_full_path, file_name)

        self._check_file_exists(user_id, full_file_path)

        self.minio.upload_file(user_id, full_file_path, file)

        db_file = self.repo.create_file_in_db(
            user_id=user_id,
            folder_id=target_folder.id if target_folder else None,
            full_path=full_file_path,
            file_size=file.size,
        )

        serializer = ResourceResponseSerializer(db_file)
        return serializer.data

    def _split_path_and_name(self, file_path: str) -> tuple[str, str]:
        file_path = file_path.strip("/")

        if "/" in file_path:
            parts = file_path.rsplit("/", 1)
            return parts[0], parts[1]

        return "", file_path

    def _build_folder_full_path(self, base_path: str, parent_path: str) -> str:
        if base_path:
            if parent_path:
                return f"{base_path}/{parent_path}/"
            return f"{base_path}/"
        else:
            if parent_path:
                return f"{parent_path}/"
            return ""

    def _get_or_create_target_folder(
        self, user_id: int, folder_full_path: str, root_folder: Folder
    ) -> Folder:
        if folder_full_path:
            folder_path_to_create = folder_full_path.rstrip("/")
            return self._ensure_folder_path(user_id, folder_path_to_create)

        return root_folder

    def _build_file_full_path(self, folder_full_path: str, file_name: str) -> str:
        if folder_full_path:
            return f"{folder_full_path}{file_name}"
        return file_name

    def _check_file_exists(self, user_id: int, full_file_path: str) -> None:
        if self.repo.get_file_or_none(user_id, full_file_path):
            raise ConflictError(f"File '{full_file_path}' already exists")

        if self.minio.is_file_exists(user_id, full_file_path):
            raise ConflictError(f"File '{full_file_path}' already exists in storage")

    def _ensure_folder_path(self, user_id: int, path: str) -> Folder:

        if not path:
            return self.repo.get_or_create_root_folder(user_id)

        path = path.strip("/")
        folder_full_path = f"{path}/"
        folder = self.repo.get_folder_or_none(user_id, folder_full_path)
        if folder:
            return folder

        parts = path.split("/")
        current_path = ""
        parent_folder = None

        for part in parts:
            if not part:
                continue

            current_path = f"{current_path}/{part}" if current_path else part
            folder_path = f"{current_path}/"

            folder = self.repo.get_folder_or_none(user_id, folder_path)
            if not folder:
                folder = self.repo.create_folder(user_id, folder_path)

            parent_folder = folder

        return parent_folder
