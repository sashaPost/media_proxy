from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List


class AppConfig(BaseSettings):
    API_KEY: str = Field(..., env="API_KEY")
    ALLOWED_DIRECTORIES: List[str] = ["images", "files"]
    MEDIA_FILES_DEST: str = "media"
    # DEBUG: bool = False
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
