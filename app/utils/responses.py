"""
Standardized API response utilities.
Provides consistent response formatting across all endpoints.
"""
from typing import Any, Dict, Optional
from flask import jsonify, Response


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = 200
) -> tuple[Response, int]:
    """
    Create a standardized success response.

    Args:
        data: The response data
        message: Optional success message
        status_code: HTTP status code (default: 200)

    Returns:
        Tuple of (jsonify response, status_code)
    """
    response = {'status': 'ok'}

    if message:
        response['message'] = message

    if data is not None:
        if isinstance(data, dict):
            response.update(data)
        else:
            response['data'] = data

    return jsonify(response), status_code


def error_response(
    error: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None
) -> tuple[Response, int]:
    """
    Create a standardized error response.

    Args:
        error: The error message
        status_code: HTTP status code (default: 400)
        details: Optional additional error details

    Returns:
        Tuple of (jsonify response, status_code)
    """
    response = {
        'status': 'error',
        'error': error
    }

    if details:
        response['details'] = details

    return jsonify(response), status_code


def validation_error_response(
    field: str,
    message: str
) -> tuple[Response, int]:
    """
    Create a validation error response.

    Args:
        field: The field that failed validation
        message: The validation error message

    Returns:
        Tuple of (jsonify response, status_code)
    """
    return error_response(
        error='Validation error',
        status_code=400,
        details={
            'field': field,
            'message': message
        }
    )
