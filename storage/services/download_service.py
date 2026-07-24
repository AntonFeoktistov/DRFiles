import io
import zipfile
from urllib.parse import quote

from django.http import StreamingHttpResponse
from rest_framework.exceptions import NotFound

from storage.services.minio_service import MinioService
from storage.services.repository import StorageRepository


class DownloadService:
    def __init__(self, minio_client: MinioService, repository: StorageRepository):
        self.minio = minio_client
        self.repo = repository

    def download_file(self, user_id: int, file_path: str) -> StreamingHttpResponse:
        file = self.repo.get_file_or_none(user_id, file_path)
        if not file:
            raise NotFound(f"File '{file_path}' not found")

        try:
            file_content = self.minio.download_file(user_id, file_path)

            if hasattr(file_content, "streaming_content"):
                response = StreamingHttpResponse(
                    file_content.streaming_content,
                    content_type="application/octet-stream",
                )
            else:
                response = StreamingHttpResponse(
                    file_content, content_type="application/octet-stream"
                )

            encoded_filename = quote(file.name, encoding="utf-8")
            response["Content-Disposition"] = (
                f'attachment; filename="{file.name}"; '
                f"filename*=UTF-8''{encoded_filename}"
            )
            response["Content-Length"] = str(file.size)

            return response

        except Exception as e:
            raise Exception(f"Storage error: {str(e)}")

    def download_folder(self, user_id: int, folder_path: str) -> StreamingHttpResponse:
        folder = self.repo.get_folder_or_none(user_id, folder_path)
        if not folder:
            raise NotFound(f"Folder '{folder_path}' not found")

        all_files = self.repo.get_files_by_prefix(user_id, folder_path)

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_obj in all_files:
                try:
                    file_content = self.minio.download_file(user_id, file_obj.full_path)

                    relative_path = file_obj.full_path

                    if isinstance(file_content, bytes):
                        zip_file.writestr(relative_path, file_content)
                    else:
                        zip_file.writestr(relative_path, file_content.getvalue())

                except Exception:
                    continue

        zip_buffer.seek(0)

        if folder_path:
            folder_name = folder_path.rstrip("/").split("/")[-1] or "folder"
        else:
            folder_name = "root"

        encoded_name = quote(folder_name, encoding="utf-8")

        response = StreamingHttpResponse(zip_buffer, content_type="application/zip")
        response["Content-Disposition"] = (
            f'attachment; filename="{folder_name}.zip"; '
            f"filename*=UTF-8''{encoded_name}.zip"
        )
        response["Content-Length"] = str(zip_buffer.getbuffer().nbytes)

        return response
