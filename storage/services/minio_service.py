import os
from io import BytesIO
from typing import List, Optional

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()


class MinioService:
    def __init__(self):
        self.client = self._make_s3_client()
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "user-files")
        self._ensure_bucket_exists()

    def _make_s3_client(self):
        endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        return boto3.client(
            "s3",
            endpoint_url=f"http://{endpoint}"
            if not os.getenv("MINIO_USE_SSL", "false").lower() == "true"
            else f"https://{endpoint}",
            aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            region_name="us-east-1",
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def _ensure_bucket_exists(self):
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                self.client.create_bucket(Bucket=self.bucket_name)
            else:
                raise

    def _get_minio_path(self, user_id: int, file_path: str) -> str:
        if not file_path:
            return f"user-{user_id}-files"
        return f"user-{user_id}-files/{file_path}"

    def is_file_exists(self, user_id: int, file_path: str) -> bool:
        full_path = self._get_minio_path(user_id, file_path)
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=full_path)
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                return False
            raise

    def upload_file(
        self, user_id: int, file_path: str, file_obj, content_type: Optional[str] = None
    ) -> None:
        full_path = self._get_minio_path(user_id, file_path)
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        if isinstance(file_obj, str):
            with open(file_obj, "rb") as f:
                self.client.upload_fileobj(
                    f, self.bucket_name, full_path, ExtraArgs=extra_args
                )
        else:
            self.client.upload_fileobj(
                file_obj, self.bucket_name, full_path, ExtraArgs=extra_args
            )

    def download_file(self, user_id: int, file_path: str) -> BytesIO:
        full_path = self._get_minio_path(user_id, file_path)
        try:
            file_obj = BytesIO()
            self.client.download_fileobj(self.bucket_name, full_path, file_obj)
            file_obj.seek(0)
            return file_obj
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                raise FileNotFoundError(f"File '{full_path}' not found in MinIO")
            raise

    def delete_file(self, user_id: int, file_path: str) -> None:
        full_path = self._get_minio_path(user_id, file_path)
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=full_path)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                pass
            else:
                raise

    def delete_files(self, user_id: int, file_paths: List[str]) -> None:
        if not file_paths:
            return

        full_paths = [self._get_minio_path(user_id, path) for path in file_paths]
        objects_to_delete = [{"Key": path} for path in full_paths]

        try:
            self.client.delete_objects(
                Bucket=self.bucket_name,
                Delete={"Objects": objects_to_delete, "Quiet": True},
            )
        except ClientError as e:
            print(f"Error during batch delete: {str(e)}")
            for path in full_paths:
                try:
                    self.client.delete_object(Bucket=self.bucket_name, Key=path)
                except ClientError:
                    pass

    def get_file_info(self, user_id: int, file_path: str) -> dict:
        full_path = self._get_minio_path(user_id, file_path)
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=full_path)
            return {
                "size": response["ContentLength"],
                "content_type": response.get("ContentType", "application/octet-stream"),
                "last_modified": response["LastModified"],
                "etag": response["ETag"],
            }
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                raise FileNotFoundError(f"File '{file_path}' not found in MinIO")
            raise

    def copy_file(self, user_id: int, source_path: str, dest_path: str) -> None:
        full_source = self._get_minio_path(user_id, source_path)
        full_dest = self._get_minio_path(user_id, dest_path)
        try:
            copy_source = {"Bucket": self.bucket_name, "Key": full_source}
            self.client.copy_object(
                Bucket=self.bucket_name, Key=full_dest, CopySource=copy_source
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                raise FileNotFoundError(f"Source file '{source_path}' not found")
            raise

    def move_file(self, user_id: int, source_path: str, dest_path: str) -> None:
        try:
            self.copy_file(user_id, source_path, dest_path)
            self.delete_file(user_id, source_path)
        except Exception as e:
            raise Exception(f"Failed to move file: {str(e)}")


_minio_service = None


def get_minio_service() -> MinioService:
    global _minio_service
    if _minio_service is None:
        _minio_service = MinioService()
    return _minio_service
