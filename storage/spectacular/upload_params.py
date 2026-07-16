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
