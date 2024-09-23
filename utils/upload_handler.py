from extensions.logger import logger
from flask import request, Response
import os
from utils.path_utils import allowed_path_and_extension, path_secure


def handle_upload(origin_file_path):
    """Coordinates the file upload process, performing validations and saving.

    Handles the following steps:
        * Checks if a valid file ('image' or 'file') is present in the request.
        * Validates the file size against the configured maximum limit.
        * Checks for an empty filename.
        * Ensures the file path is allowed and has a supported extension.
        * Secures the destination path.
        * Saves the uploaded file to disk and sets appropriate permissions.

    Args:
        origin_file_path (str): The relative file path provided in the request.

    Returns:
        True:  If the upload process is successful.
        False: If any validation fails or an error occurs during the upload.
        Response:  If no suitable file is found in the request or the file
        size is too large.
    """
    logger.info("*** 'handle_upload' was triggered ***")
    logger.info(f"'origin_file_path': {origin_file_path}")
    logger.info(f"'request.files': {request.files}")

    if "image" not in request.files and "file" not in request.files:
        logger.warning(f"'request.files': {request.files}")
        return Response("No file part", status=400)

    file_key = "image" if "image" in request.files else "file"
    try:
        uploaded_file = request.files[file_key]
        logger.info(f"'uploaded_file': {uploaded_file}")

        if uploaded_file.filename == "":
            logger.warning("uploaded_file.filename == ''")
            return Response("Empty filename", status=400)

        try:
            if allowed_path_and_extension(origin_file_path):
                logger.info("passed 'if allowed_path_and_extension(origin_file_path)'")
                secured_path = path_secure(origin_file_path, file_key)
                logger.info(f"'secured_path': {secured_path}")

                with open(secured_path, "wb") as destination_file:
                    uploaded_file.save(destination_file)
                os.chmod(secured_path, 0o755)
                logger.info("SUCCESS")
                return True
            else:
                logger.warning("!!! 'allowed_path_and_extension' failed !!!")
                return False
        except Exception as e:
            logger.info(f"Exception: {e}")
            logger.warning(f"!!! 'handle_upload' failed !!!")
            return False
    except Exception as e:
        logger.info(f"Exception: {e}")
        return False
