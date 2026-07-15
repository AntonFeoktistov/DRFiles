from typing import List, Optional

from django.core.exceptions import ValidationError
from django.db import transaction

from storage.models import File, Folder
from storage.services import utils


class StorageRepository:
    def get_folder_or_none(self, user_id: int, folder_path: str) -> Optional[Folder]:
        try:
            return Folder.objects.get(user_id=user_id, full_path=folder_path)
        except Folder.DoesNotExist:
            return None

    def get_file_or_none(self, user_id: int, file_path: str) -> Optional[File]:
        try:
            return File.objects.get(user_id=user_id, full_path=file_path)
        except File.DoesNotExist:
            return None

    @transaction.atomic
    def create_folder(self, user_id: int, folder_path: str) -> Folder:
        existing = self.get_folder_or_none(user_id, folder_path)
        if existing:
            raise ValidationError(f"Folder {folder_path} is already exists")

        folder_name, parent_path = utils.get_name_and_parent_path(folder_path)

        parent = None
        if parent_path:
            parent = self.get_folder_or_none(user_id, parent_path)
            if not parent:
                raise ValidationError(f"Parent folder not found: {parent_path}")

        folder = Folder.objects.create(
            user_id=user_id, name=folder_name, folder=parent, full_path=folder_path
        )

        return folder

    def get_or_create_root_folder(self, user_id: int) -> Folder:
        existing = Folder.objects.filter(user_id=user_id, full_path="").first()
        if existing:
            return existing

        return Folder.objects.create(
            user_id=user_id, name="", folder=None, full_path=""
        )

    @transaction.atomic
    def create_file_in_db(
        self, user_id: int, folder_id: int, full_path: str, file_size: int
    ) -> File:
        file_name, _ = utils.get_name_and_parent_path(full_path)

        file = File.objects.create(
            user_id=user_id,
            name=file_name,
            folder_id=folder_id,
            full_path=full_path,
            size=file_size,
        )

        return file

    def get_files_by_parent(self, user_id: int, parent: Folder) -> List[File]:
        return list(File.objects.filter(user_id=user_id, folder=parent))

    def get_folders_by_parent(self, user_id: int, parent: Folder) -> List[Folder]:
        return list(Folder.objects.filter(user_id=user_id, parent=parent))

    def get_files_by_query(self, user_id: int, query: str) -> List[File]:
        return list(File.objects.filter(user_id=user_id, name__icontains=query))

    def get_folders_by_query(self, user_id: int, query: str) -> List[Folder]:
        return list(Folder.objects.filter(user_id=user_id, name__icontains=query))

    def get_files_by_prefix(self, user_id: int, prefix: str) -> List[File]:
        return list(File.objects.filter(user_id=user_id, full_path__startswith=prefix))

    def get_folders_by_prefix(self, user_id: int, prefix: str) -> List[Folder]:
        return list(
            Folder.objects.filter(
                user_id=user_id, full_path__startswith=prefix
            ).exclude(full_path=prefix)
        )
