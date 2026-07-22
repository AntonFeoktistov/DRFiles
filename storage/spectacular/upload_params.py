from drf_spectacular.utils import OpenApiParameter

upload_parameters = [
    OpenApiParameter(
        name="path",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Базовая папка для загрузки",
        required=False,
    )
]

upload_request = {
    "multipart/form-data": {
        "type": "object",
        "properties": {
            "object": {
                "type": "array",
                "items": {"type": "string", "format": "binary"},
                "description": "Select files to upload",
            },
            "paths": {
                "type": "string",
                "description": "JSON array of paths for each file",
                "example": '["documents/report.pdf", "subfolder/file.txt"]',
            },
        },
        "required": ["object"],
    }
}
