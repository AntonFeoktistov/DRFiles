from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

search_parameters = [
    OpenApiParameter(
        name="query",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Search query",
        required=False,
        default="",
    ),
]
