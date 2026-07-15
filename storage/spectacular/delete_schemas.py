from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes

delete_parameters = [
    OpenApiParameter(
        name="path",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Path to the resource to delete (file or folder)",
        required=True,
    ),
]

delete_responses = {
    204: {
        "description": "Resource deleted successfully (No Content)",
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
        "properties": {"detail": {"type": "string", "example": "Resource not found"}},
    },
    500: {
        "description": "Internal Server Error",
        "type": "object",
        "properties": {
            "detail": {"type": "string", "example": "Internal server error"}
        },
    },
}
