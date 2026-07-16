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

directory_create_parameters = [
    OpenApiParameter(
        name="path",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Full path of the folder to create (including parent path)",
        required=True,
    ),
]
