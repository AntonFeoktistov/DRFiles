from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, AuthenticationFailed):
        return Response(
            {"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )

    if isinstance(exc, NotAuthenticated):
        return Response(
            {"message": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, ValidationError):
        error_str = str(exc)
        if "username" in error_str.lower() and "already exists" in error_str.lower():
            return Response(
                {"message": "Username already exists"}, status=status.HTTP_409_CONFLICT
            )
        if hasattr(exc, "detail"):
            return Response(
                {"message": _extract_error_message(exc.detail)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    response = exception_handler(exc, context)
    if response is not None:
        error_message = _extract_error_message(response.data)
        return Response({"message": error_message}, status=response.status_code)

    return Response(
        {"message": "Internal server error"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _extract_error_message(data):
    if isinstance(data, str):
        return data

    if isinstance(data, dict):
        messages = []
        for field, errors in data.items():
            if field == "non_field_errors":
                messages.extend(str(e) for e in errors)
            else:
                if isinstance(errors, list):
                    for error in errors:
                        messages.append(str(error))
                else:
                    messages.append(str(errors))
        return "; ".join(messages) if messages else "Validation error"

    if isinstance(data, list):
        return "; ".join(str(item) for item in data)

    return str(data)
