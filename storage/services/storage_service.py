from storage.services.minio_service import get_minio_service


class StorageService:
    def __init__(self):
        self.minio_client = get_minio_service()

    def get_resource(self, path):
        return path
