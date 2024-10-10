from extensions.logger import logger
import os
from config.app_config import AppConfig


def initialize_directories(app):
    """
    Creates media directories if they don't exist.
    This function should be called once during app initialization.
    """
    config = AppConfig()
    logger.info("Checking and creating media directories if necessary")
    try:
        if not os.path.exists(config.MEDIA_FILES_DEST):
            os.makedirs(config.MEDIA_FILES_DEST, exist_ok=True)
            logger.info(f"Created main media directory: {config.MEDIA_FILES_DEST}")

        for directory in config.ALLOWED_DIRECTORIES:
            dest_dir = os.path.join(config.MEDIA_FILES_DEST, directory)
            os.makedirs(dest_dir, exist_ok=True)
            logger.info(f"Created subdirectory: {dest_dir}")
    except OSError as e:
        logger.error(f"Failed to create directory: {e}")


def setup_app(app):
    """
    Performs necessary setup steps for the application.
    This function should be called once during app initialization.
    """
    initialize_directories(app)
