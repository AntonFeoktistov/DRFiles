from django.db import transaction
from minio import S3Error
from rest_framework.exceptions import NotFound

from storage.services.minio_service import MinioService
from storage.services.repository import StorageRepository


class DeleteService:
    def __init__(self, minio_client: MinioService, repository: StorageRepository):
        self.minio = minio_client
        self.repo = repository

    @transaction.atomic
    def delete_file(self, user_id: int, file_path: str) -> None:
        file = self.repo.get_file_or_none(user_id, file_path)
        if not file:
            raise NotFound(f"File '{file_path}' not found")

        try:
            self.minio.delete_file(user_id, file_path)
        except S3Error as e:
            if e.code != "NoSuchKey":
                raise Exception(f"MinIO error: {e}")
        file.delete()

    @transaction.atomic
    def delete_folder(self, user_id: int, folder_path: str) -> None:
        folder = self.repo.get_folder_or_none(user_id, folder_path)
        if not folder:
            raise NotFound(f"File '{folder_path}' not found")

        files = self.repo.get_files_by_prefix(user_id, folder_path)

        minio_errors = []
        for file_obj in files:
            try:
                self.minio.delete_file(user_id, file_obj.full_path)
            except S3Error as e:
                if e.code != "NoSuchKey":
                    minio_errors.append(f"{file_obj.full_path}: {e}")

        if minio_errors:
            raise Exception(f"MinIO errors: {', '.join(minio_errors)}")

        for file_obj in files:
            file_obj.delete()

        descendants = self.repo.get_folders_by_prefix(user_id, folder_path)
        for subfolder in descendants:
            subfolder.delete()
        folder.delete()
