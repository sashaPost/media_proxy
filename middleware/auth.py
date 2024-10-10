from collections.abc import Callable
from typing import Optional
from flask import request, jsonify
from functools import wraps
from config.app_config import AppConfig


class AuthMiddleware:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def get_api_key(self) -> str:
        return self.config.API_KEY

    def get_api_key_header(self) -> str:
        return "Authorization"

    def check_api_key(self, func: Optional[Callable] = None) -> Callable:
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapper(*args, **kwargs):
                api_key = self.get_api_key()
                header_name = self.get_api_key_header()

                if request.headers.get(header_name) != api_key:
                    return jsonify({"error": "Unauthorized"}), 401
                return f(*args, **kwargs)

            return wrapper

        if func:
            return decorator(func)
        return decorator


def create_auth_middleware(config: AppConfig) -> AuthMiddleware:
    return AuthMiddleware(config)
