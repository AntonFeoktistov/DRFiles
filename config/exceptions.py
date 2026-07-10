from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):

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
            if isinstance(errors, list):
                messages.extend(str(e) for e in errors)
            elif isinstance(errors, str):
                messages.append(errors)
            else:
                messages.append(str(errors))
        return "; ".join(messages) if messages else "Validation error"

    if isinstance(data, list):
        return "; ".join(str(item) for item in data)

    return str(data)
