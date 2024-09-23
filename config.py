from dotenv import load_dotenv
import os
import secrets

load_dotenv()


class Config:
    SECRET_KEY = str(secrets.SystemRandom().getrandbits(128))
    MAX_CONTENT_LENGTH = 24 * 1024 * 1024  # Limit file size to 24MB
    API_KEY = os.getenv("API_KEY")
    ALLOWED_EXTENSIONS = {
        "image": set(["jpeg", "jpg", "png", "gif"]),
        "document": set(["docx", "pdf", "doc"]),
    }
    ALLOWED_DIRECTORIES = ["images", "files"]
    MEDIA_FILES_DEST = "media"
    ENV = os.environ.get("ENV", "development") == "production"
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
