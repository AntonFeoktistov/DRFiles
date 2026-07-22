from typing import List

from rest_framework.exceptions import NotFound, ParseError

from config.exceptions import ConflictError
from storage.services import path_utils
from storage.services.delete_service import DeleteService
from storage.services.download_service import DownloadService
from storage.services.minio_service import get_minio_service
from storage.services.move_service import MoveService
from storage.services.repository import StorageRepository
from storage.services.upload_service import UploadService


class StorageService:
    def __init__(self):
        self.minio = get_minio_service()
        self.repo = StorageRepository()
        self.upload = UploadService(self.minio, self.repo)
        self.delete = DeleteService(self.minio, self.repo)
        self.download = DownloadService(self.minio, self.repo)
        self.move = MoveService(self.minio, self.repo)

    def get_resource(self, user_id: int, path: str):
        if path_utils.is_resource_folder(path):
            resource = self.repo.get_folder_or_none(user_id, path)
        else:
            resource = self.repo.get_file_or_none(user_id, path)
        return resource

    def upload_resources(
        self, user_id: int, base_path: str, files_with_paths: List[tuple]
    ):
        return self.upload.upload_files(user_id, base_path, files_with_paths)

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

    def get_folder_resources(self, user_id: int, folder_path: str):
        folder = self.repo.get_folder_or_none(user_id, folder_path)
        if not folder:
            raise NotFound(f"{folder_path} is not found")
        files = self.repo.get_files_by_parent(user_id, folder)
        folders = self.repo.get_folders_by_parent(user_id, folder)
        return files + folders

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
