from fastapi import HTTPException, Depends, Header
from fastapi.security import APIKeyHeader
from config.app_config import AppConfig


class AuthMiddleware:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

    async def verify_api_key(
        self, api_key: str = Depends(APIKeyHeader(name="Authorization"))
    ):
        if api_key != self.config.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        return True


def create_auth_middleware(config: AppConfig) -> AuthMiddleware:
    return AuthMiddleware(config)
