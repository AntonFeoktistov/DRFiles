from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

download_parameters = [
    OpenApiParameter(
        name="path",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Path to the file or folder to download",
        required=False,
    ),
]

download_responses = {
    200: {
        "description": "File content or ZIP archive with folder contents",
        "content": {
            "application/octet-stream": {
                "schema": {
                    "type": "string",
                    "format": "binary",
                }
            },
            "application/zip": {
                "schema": {
                    "type": "string",
                    "format": "binary",
                }
            },
        },
    },
    400: {
        "description": "Bad Request - Invalid or missing path",
        "type": "object",
        "properties": {"detail": {"type": "string", "example": "Path is required"}},
    },
    401: {
        "description": "Unauthorized - User not authenticated",
        "type": "object",
        "properties": {
            "detail": {
                "type": "string",
                "example": "Authentication credentials were not provided.",
            }
        },
    },
    404: {
        "description": "Not Found - Resource does not exist",
        "type": "object",
        "properties": {
            "detail": {
                "type": "string",
                "example": "Resource 'documents/report.pdf' not found",
            }
        },
    },
    500: {
        "description": "Internal Server Error",
        "type": "object",
        "properties": {
            "detail": {"type": "string", "example": "Internal server error"}
        },
    },
}
