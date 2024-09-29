from flask import request, jsonify
from functools import wraps
import os


def check_api_key(func):
    """
    A Flask middleware for API key authentication.

    This middleware intercepts requests and verifies the presence and validity
    of an API key in the Authorization header.

    Args:
        func (function): The decorated function to be protected.

    Returns:
        function: The wrapped function with API key authentication.

    Raises:
        HTTPException (401): If the API key is missing or invalid.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        expected_header = os.environ.get("API_KEY_HEADER", "Authorization")
        if request.headers.get(expected_header) != os.environ.get("API_KEY"):
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)

    return wrapper
