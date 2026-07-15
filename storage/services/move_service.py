from botocore.exceptions import ClientError
from django.db import transaction
from rest_framework.exceptions import NotFound, ParseError

from config.exceptions import ConflictError
from storage.models import Folder
from storage.services import path_utils
from storage.services.minio_service import MinioService
from storage.services.repository import StorageRepository


class MoveService:
    def __init__(self, minio_client: MinioService, repository: StorageRepository):
        self.minio = minio_client
        self.repo = repository

    @transaction.atomic
    def move_file(self, user_id: int, path_from: str, path_to: str):
        self._check_types_for_same(path_from, path_to)

        file_from = self.repo.get_file_or_none(user_id, path_from)
        if not file_from:
            raise NotFound(f"File '{path_from}' not found")

        if self.repo.get_file_or_none(user_id, path_to):
            raise ConflictError(f"File '{path_to}' already exists")

        file_name, folder_path = path_utils.get_name_and_parent_path(path_to)
        folder = self.repo.get_folder_or_none(user_id, folder_path)
        if not folder:
            raise NotFound(f"Parent folder '{folder_path}' not found")

        try:
            self.minio.move_file(user_id, path_from, path_to)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise NotFound(f"File '{path_from}' not found in storage")
            raise Exception(f"MinIO error: {str(e)}")

        file_from.full_path = path_to
        file_from.name = file_name
        file_from.folder = folder
        file_from.save()

        return file_from

    @transaction.atomic
    def move_folder(self, user_id: int, path_from: str, path_to: str):
        self._check_types_for_same(path_from, path_to)

        folder_from = self.repo.get_folder_or_none(user_id, path_from)
        if not folder_from:
            raise NotFound(f"Folder '{path_from}' not found")

        if self.repo.get_folder_or_none(user_id, path_to):
            raise ConflictError(f"Folder '{path_to}' already exists")

        _, parent_path = path_utils.get_name_and_parent_path(path_to)
        if parent_path:
            parent_folder = self.repo.get_folder_or_none(user_id, parent_path)
            if not parent_folder:
                raise NotFound(f"Parent folder '{parent_path}' not found")

        try:
            updated_folders = self._update_folders_and_subfolders_paths(
                user_id, path_from, path_to
            )
            self._move_files_and_update_paths(
                user_id, path_from, path_to, updated_folders
            )

            return self.repo.get_folder_or_none(user_id, path_to)

        except Exception as e:
            raise Exception(f"Error moving folder: {str(e)}")

    def _update_folders_and_subfolders_paths(
        self,
        user_id: int,
        path_from: str,
        path_to: str,
    ) -> dict[str, Folder]:
        updated_folders = {}

        folder = self.repo.get_folder_or_none(user_id, path_from)
        if not folder:
            raise NotFound(f"Folder '{path_from}' not found")

        self._update_folder_path(folder, path_from, path_to, updated_folders)

        subfolders = self.repo.get_folders_by_prefix(user_id, path_from)
        for subfolder in subfolders:
            self._update_folder_path(subfolder, path_from, path_to, updated_folders)

        self._set_parent_ids(updated_folders)

        for folder in updated_folders.values():
            folder.save()

        return updated_folders

    def _set_parent_ids(self, folders: dict[str, Folder]) -> None:
        for folder in folders.values():
            _, parent_path = path_utils.get_name_and_parent_path(folder.full_path)
            if parent_path in folders:
                folder.parent_id = folders[parent_path].id
            else:
                folder.parent_id = None

    def _move_files_and_update_paths(
        self,
        user_id: int,
        path_from: str,
        path_to: str,
        updated_folders: dict[str, Folder],
    ) -> None:
        files = self.repo.get_files_by_prefix(user_id, path_from)

        for file_obj in files:
            old_path = file_obj.full_path
            new_path = old_path.replace(path_from, path_to, 1)

            _, parent_path = path_utils.get_name_and_parent_path(new_path)
            folder_id = self._get_folder_id_for_path(
                user_id, parent_path, updated_folders
            )

            self.minio.move_file(user_id, old_path, new_path)

            file_obj.full_path = new_path
            file_obj.name, _ = path_utils.get_name_and_parent_path(new_path)
            file_obj.folder_id = folder_id
            file_obj.save()

    def _update_folder_path(
        self,
        folder: Folder,
        path_from: str,
        path_to: str,
        folders_dict: dict[str, Folder],
    ) -> str:
        old_full = folder.full_path
        new_full = old_full.replace(path_from, path_to, 1)
        folder.full_path = new_full
        folder.name, _ = path_utils.get_name_and_parent_path(new_full)
        folders_dict[new_full] = folder
        return folder.full_path

    def _get_folder_id_for_path(
        self, user_id: int, folder_path: str, updated_folders: dict[str, Folder]
    ) -> int:
        """Получает ID папки по пути (из кэша или БД)"""
        if not folder_path:
            root = self.repo.get_or_create_root_folder(user_id)
            return root.id

        if folder_path in updated_folders:
            return updated_folders[folder_path].id

        folder = self.repo.get_folder_or_none(user_id, folder_path)
        if not folder:
            raise NotFound(f"Parent folder '{folder_path}' not found")
        return folder.id

    def _check_types_for_same(self, path_from: str, path_to: str) -> None:
        are_types_same = path_utils.is_resource_folder(
            path_from
        ) == path_utils.is_resource_folder(path_to)
        if not are_types_same:
            raise ParseError(
                f"Resources '{path_from}' and '{path_to}' have different types"
            )
