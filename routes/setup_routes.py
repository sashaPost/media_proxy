from flask import app, Blueprint
from extensions.logger import logger
import os

setup_bp = Blueprint("setup", __name__)


@setup_bp.before_app_request
def directories_check():
    """
    Creates media directories on first request.
    """
    logger.info("*** 'directories_check' was triggered ***")
    # dest_dir = None
    try:
        os.makedirs(app.config["MEDIA_FILES_DEST"], exist_ok=True)
        for directory in app.config["ALLOWED_DIRECTORIES"]:
            dest_dir = os.path.join(app.config["MEDIA_FILES_DEST"], directory)
            os.makedirs(dest_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create directory {dest_dir}: {e}")