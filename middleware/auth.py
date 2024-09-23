from flask import app, request, jsonify
from extensions.logger import logger
from functools import wraps


def check_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Request API key: {request.headers.get('Authorization')}")
        # logger.info(f"Source API key: {app.config["API_KEY"]}")
        if request.headers.get("Authorization") != app.config["API_KEY"]:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)

    return wrapper
