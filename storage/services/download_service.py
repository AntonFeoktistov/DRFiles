import io
import zipfile
from urllib.parse import quote

from django.http import StreamingHttpResponse

from storage.services.minio_service import MinioService
from storage.services.repository import StorageRepository


class DownloadService:
    def __init__(self, minio_client: MinioService, repository: StorageRepository):
        self.minio = minio_client
        self.repo = repository

    def download_file(self, user_id: int, file_path: str) -> StreamingHttpResponse:

        file = self.repo.get_file_or_none(user_id, file_path)
        if not file:
            raise FileNotFoundError(f"File '{file_path}' not found")

        try:
            file_content = self.minio.download_file(user_id, file_path)
            encoded_filename = quote(file.name, encoding="utf-8")
            response = StreamingHttpResponse(
                file_content, content_type="application/octet-stream"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{encoded_filename}"'
            )
            response["Content-Length"] = str(file.size)

            return response

        except Exception as e:
            raise Exception(f"MinIO error: {str(e)}")

    def download_folder(self, user_id: int, folder_path: str) -> StreamingHttpResponse:

        folder = self.repo.get_folder_or_none(user_id, folder_path)
        if not folder:
            raise FileNotFoundError(f"Folder '{folder_path}' not found")

        all_files = self.repo.get_files_by_prefix(user_id, folder_path)
        if not all_files:
            raise FileNotFoundError("Folder is empty")

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_obj in all_files:
                try:
                    file_content = self.minio.download_file(user_id, file_obj.full_path)
                    relative_path = file_obj.full_path
                    if folder_path:
                        relative_path = file_obj.full_path.replace(
                            folder_path, "", 1
                        ).lstrip("/")

                    zip_file.writestr(relative_path, file_content.getvalue())

                except FileNotFoundError:
                    continue
                except Exception as e:
                    raise Exception(
                        f"MinIO error while downloading '{file_obj.full_path}': {str(e)}"
                    )

        zip_buffer.seek(0)

        folder_name = folder.name or "folder"
        encoded_name = quote(folder_name, encoding="utf-8")

        response = StreamingHttpResponse(zip_buffer, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{encoded_name}.zip"'
        response["Content-Length"] = str(zip_buffer.getbuffer().nbytes)

        return response
