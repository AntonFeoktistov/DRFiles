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
