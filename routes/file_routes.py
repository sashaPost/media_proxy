from flask import Blueprint, current_app, Response, send_from_directory
import os
from extensions.logger import logger
from middleware.auth import check_api_key
from utils.upload_handler import handle_upload


file_bp = Blueprint("file", __name__)


@file_bp.route("/media/<path:file_path>", methods=["GET"])
def handle_get_request(file_path):
    """
    Handles GET requests to retrieve files from the media directory.

    This function retrieves a file based on the provided `file_path` within the
    configured media directory (`MEDIA_FILES_DEST`).

    Args:
        file_path (str): The path to the requested file relative to the media
                         directory.

    Returns:
        Response: A Flask response object containing the requested file or an
                  error message depending on the outcome.

    Raises:
        FileNotFoundError: If the specified file is not found.
    """
    logger.info("'GET' method detected")

    # logger.info(f"'file_path': {file_path}")

    try:
        # logger.info(f"'os.path.dirname': {os.path.dirname(file_path)}")
        # logger.info(f"'os.path.basename': {os.path.basename(file_path)}")
        return send_from_directory(
            os.path.join(
                current_app.config["MEDIA_FILES_DEST"], os.path.dirname(file_path)
            ),
            os.path.basename(file_path),
        )
    except FileNotFoundError:
        return Response("File not found", status=404)


@file_bp.route("/media/<path:origin_file_path>", methods=["POST"])
@check_api_key
def upload_file(origin_file_path):
    """
    Handles POST requests for uploading files to the media directory.

    This function delegates the upload process to the `handle_upload` function
    and returns an appropriate response based on the outcome.

    Args:
        origin_file_path (str): The relative file path extracted from the URL,
                                 intended for the uploaded file.

    Returns:
        Response: A Flask response object indicating success (200 OK) or error
                  (501 Not Implemented) during the upload process.
    """
    logger.info("'POST' method detected")

    # logger.info("*** 'upload_file' was triggered ***")
    # logger.info(f"'origin_file_path': {origin_file_path}")

    if handle_upload(origin_file_path):
        return Response("OK", status=200)
    return Response("Error uploading file", status=501)
