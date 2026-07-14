from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes
from rest_framework import serializers


class UploadRequestSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(), required=True, help_text="Select files to upload"
    )


upload_parameters = [
    OpenApiParameter(
        name="path",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Path to upload files to",
        required=False,
    ),
]

upload_request = {
    "multipart/form-data": {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {"type": "string", "format": "binary"},
                "description": "Select files to upload",
            }
        },
    }
}

upload_responses = {
    201: {
        "description": "Files uploaded successfully",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "name": {"type": "string"},
                "size": {"type": "integer", "nullable": True},
                "type": {"type": "string"},
            },
        },
    },
    400: {"description": "Bad Request"},
    401: {"description": "Unauthorized"},
    404: {"description": "Not Found"},
    409: {"description": "File already exists"},
    500: {"description": "Internal Server Error"},
}
