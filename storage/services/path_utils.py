def is_resource_folder(path):
    return path.endswith("/") or path == ""


def get_name_and_parent_path(full_path: str):
    if not full_path:
        return "", ""

    path = full_path.rstrip("/")
    if "/" in path:
        parts = path.rsplit("/", 1)
        return parts[1], parts[0] + "/"
    return path, ""


def get_content_type(filename: str) -> str:
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    types = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "txt": "text/plain",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "zip": "application/zip",
        "rar": "application/x-rar-compressed",
        "7z": "application/x-7z-compressed",
        "mp4": "video/mp4",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "json": "application/json",
        "xml": "application/xml",
        "csv": "text/csv",
        "html": "text/html",
        "css": "text/css",
        "js": "application/javascript",
    }
    return types.get(ext, "application/octet-stream")
