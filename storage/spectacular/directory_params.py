from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

directory_get_parameters = [
    OpenApiParameter(
        name="path",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Path to the folder to list contents of",
        required=False,
        default="",
    ),
]

directory_get_responses = {
    200: {
        "description": "List of resources in the folder (non-recursive)",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the folder containing the resource",
                    "example": "documents/projects/",
                },
                "name": {
                    "type": "string",
                    "description": "Name of the resource",
                    "example": "report.pdf",
                },
                "size": {
                    "type": "integer",
                    "description": "Size of the file in bytes (omitted for folders)",
                    "nullable": True,
                    "example": 12345,
                },
                "type": {
                    "type": "string",
                    "description": "Resource type",
                    "enum": ["FILE", "DIRECTORY"],
                    "example": "FILE",
                },
            },
        },
        "examples": {
            "mixed": {
                "summary": "Folder with files and subfolders",
                "value": [
                    {"path": "documents/projects/", "name": "src", "type": "DIRECTORY"},
                    {
                        "path": "documents/projects/",
                        "name": "report.pdf",
                        "size": 12345,
                        "type": "FILE",
                    },
                    {
                        "path": "documents/projects/",
                        "name": "readme.md",
                        "size": 512,
                        "type": "FILE",
                    },
                ],
            },
            "empty": {"summary": "Empty folder", "value": []},
        },
    },
    400: {
        "description": "Bad Request - Invalid path",
        "type": "object",
        "properties": {"detail": {"type": "string", "example": "Invalid path format"}},
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
        "description": "Not Found - Folder does not exist",
        "type": "object",
        "properties": {
            "detail": {
                "type": "string",
                "example": "Folder 'documents/projects' not found",
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


directory_create_parameters = [
    OpenApiParameter(
        name="path",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Full path of the folder to create (including parent path)",
        required=True,
    ),
]

directory_create_responses = {
    201: {
        "description": "Folder created successfully",
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the folder containing the new folder",
                "example": "documents/projects/",
            },
            "name": {
                "type": "string",
                "description": "Name of the created folder",
                "example": "new_folder",
            },
            "type": {
                "type": "string",
                "description": "Resource type",
                "enum": ["DIRECTORY"],
                "example": "DIRECTORY",
            },
        },
        "examples": {
            "folder": {
                "summary": "Folder created",
                "value": {
                    "path": "documents/projects/",
                    "name": "new_folder",
                    "type": "DIRECTORY",
                },
            }
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
        "description": "Not Found - Parent folder does not exist",
        "type": "object",
        "properties": {
            "detail": {
                "type": "string",
                "example": "Parent folder 'documents/projects' not found",
            }
        },
    },
    409: {
        "description": "Conflict - Folder already exists",
        "type": "object",
        "properties": {
            "detail": {
                "type": "string",
                "example": "Folder 'documents/projects/new_folder' already exists",
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
