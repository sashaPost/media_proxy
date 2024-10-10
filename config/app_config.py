from dotenv import load_dotenv
import os
import secrets


load_dotenv()


class AppConfig:
    SECRET_KEY = str(secrets.SystemRandom().getrandbits(128))
    API_KEY = os.getenv("API_KEY")
    ALLOWED_DIRECTORIES = ["images", "files"]
    MEDIA_FILES_DEST = "media"
    ENV = os.environ.get("ENV", "development") == "production"
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
