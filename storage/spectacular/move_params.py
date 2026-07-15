from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

move_parameters = [
    OpenApiParameter(
        name="from",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Current full path of the resource (source)",
        required=False,
    ),
    OpenApiParameter(
        name="to",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="New full path of the resource (destination)",
        required=False,
    ),
]

move_responses = {
    200: {
        "description": "Resource moved/renamed successfully",
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the folder containing the resource",
                "example": "documents/",
            },
            "name": {
                "type": "string",
                "description": "Name of the resource",
                "example": "new_name.pdf",
            },
            "size": {
                "type": "integer",
                "description": "Size of the file in bytes (omitted for folders)",
                "nullable": True,
                "example": 12345,
            },
            "type": {
                "type": "string",
                "description": "Resource type (FILE or DIRECTORY)",
                "enum": ["FILE", "DIRECTORY"],
                "example": "FILE",
            },
        },
        "examples": {
            "file": {
                "summary": "File response",
                "value": {
                    "path": "documents/",
                    "name": "new_name.pdf",
                    "size": 12345,
                    "type": "FILE",
                },
            },
            "folder": {
                "summary": "Folder response",
                "value": {
                    "path": "documents/",
                    "name": "projects",
                    "type": "DIRECTORY",
                },
            },
        },
    },
    400: {
        "description": "Bad Request - Invalid or missing paths",
        "type": "object",
        "properties": {
            "detail": {
                "type": "string",
                "example": "Both 'from' and 'to' paths are required",
            }
        },
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
                "example": "Resource 'documents/old_name.pdf' not found",
            }
        },
    },
    409: {
        "description": "Conflict - Destination already exists",
        "type": "object",
        "properties": {
            "detail": {
                "type": "string",
                "example": "Resource 'documents/new_name.pdf' already exists",
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
