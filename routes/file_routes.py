from flask import app, Blueprint, Response, send_from_directory
import os
from extensions.logger import logger
from middleware.auth import check_api_key
from utils.upload_handler import handle_upload


file_bp = Blueprint("file", __name__)


@file_bp.route("/media/<path:file_path>", methods=["GET"])
def handle_get_request(file_path):
    logger.info(f"'file_path': {file_path}")
    logger.info("'GET' method detected")
    try:
        logger.info(f"'os.path.dirname': {os.path.dirname(file_path)}")
        logger.info(f"'os.path.basename': {os.path.basename(file_path)}")
        return send_from_directory(
            os.path.join(app.config["MEDIA_FILES_DEST"], os.path.dirname(file_path)),
            os.path.basename(file_path),
        )
    except FileNotFoundError:
        return Response("File not found", status=404)
    except Exception as e:
        return Response("Unsupported method", status=405)


@file_bp.route("/media/<path:origin_file_path>", methods=["POST"])
@check_api_key
def upload_file(origin_file_path):
    """Handles file upload requests.

    Performs the following:
        * Logs the request.
        * Delegates the upload process to the `handle_upload` function.
        * Returns an appropriate response (success or error) based on the
        result of `handle_upload`.

    Args:
        origin_file_path (str): The relative file path extracted from the URL.
    """
    logger.info("*** 'upload_file' was triggered ***")
    logger.info("'POST' method detected")
    logger.info(f"'origin_file_path': {origin_file_path}")

    if handle_upload(origin_file_path):
        return Response("OK", status=200)
    return Response("Error uploading file", status=501)
