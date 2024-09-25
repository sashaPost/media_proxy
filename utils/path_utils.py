from extensions.logger import logger
from flask import current_app, request, Response
import os
from werkzeug.utils import secure_filename
from utils.file_validation import is_valid_image, is_valid_file


def get_file_extension(origin_file_path):
    """Determines whether the file extension in the provided path is allowed.

    Checks if the extracted file extension exists in the list of allowed
    extensions for images or documents.

    Args:
        origin_file_path (str): The file path to be analyzed.

    Returns:
        bool: True if the file extension is supported, False otherwise.
    """
    # logger.info("*** 'get_file_extension' was triggered ***")
    file_extension = origin_file_path.split(".")[-1]
    # logger.info(f"'file_extension': {file_extension}")

    if (
        file_extension not in current_app.config["ALLOWED_EXTENSIONS"]["image"]
        and file_extension not in current_app.config["ALLOWED_EXTENSIONS"]["document"]
    ):
        return False
    return True


def get_request_directory(req_abs_file_path):
    """Splits the absolute file path by the '/' separator and rejoins all
    elements except the last one (the filename), providing the directory.

    Args:
        req_abs_file_path (str): The absolute file path to process.

    Returns:
        str: The extracted directory absolute path.
    """
    # logger.info("*** 'get_request_directory' was triggered ***")
    # logger.info(f"'req_abs_file_path': {req_abs_file_path}")

    parts = req_abs_file_path.split("/")
    # logger.info(f"directory: {'/'.join(parts[:-1])}")
    return "/".join(parts[:-1])


def is_valid_file_path(origin_file_path):
    """Validates a file path for security and allowed locations.

    Checks if the constructed absolute file path:
        * Resides within the configured media directory.
        * Points to an existing directory.
        * Belongs to a specifically allowed subdirectory.

    Args:
        origin_file_path (str): The relative file path provided in the request.

    Returns:
        bool: True if the file path is valid, False otherwise.
    """
    # logger.info(f"*** 'is_valid_file_path' was triggered ***")
    #
    # logger.info(f"'origin_file_path': {origin_file_path}")

    req_abs_file_path = os.path.abspath(
        os.path.normpath(
            os.path.join(current_app.config["MEDIA_FILES_DEST"], origin_file_path)
        )
    )
    logger.info(f"'req_abs_file_path': {req_abs_file_path}")

    media_abs_path = os.path.abspath(current_app.config["MEDIA_FILES_DEST"])
    logger.info(f"'media_abs_path': {media_abs_path}")

    allowed_dirs = [
        os.path.join(media_abs_path, directory)
        for directory in current_app.config["ALLOWED_DIRECTORIES"]
    ]
    logger.info(f"'allowed_dirs': {allowed_dirs}")

    req_dir = get_request_directory(req_abs_file_path)
    logger.info(f"'req_dir': {req_dir}")

    if os.path.exists(req_dir) and req_abs_file_path.startswith(media_abs_path):
        if req_dir in allowed_dirs:
            return True
    logger.warning(f"'req_abs_file_path': {req_abs_file_path}")
    logger.warning(f"!!! 'is_valid_file_path' FAILED !!!")
    return False


def path_secure(origin_file_path, file_key):
    """Secures the destination path for an uploaded file.

    Determines the appropriate subdirectory ('images' or 'files') based on
    file type and constructs a safe, sanitized filename.

    Args:
        origin_file_path (str): The original file path provided by the user.
        file_key (str): Key in the 'request.files' dictionary ('image' or
        'file').

    Returns:
        str: The secured file path ready for saving the uploaded file.
        None: If a directory traversal is attempted.
        False: If an invalid file type is detected.
    """
    logger.info("*** 'path_secure' triggered ***")

    logger.info(f"'file_key': {file_key}")

    uploaded_file = request.files[file_key]
    logger.info(f"'uploaded_file': {uploaded_file}")

    secured_filename = secure_filename(uploaded_file.filename)
    logger.info(f"'file_name': {secured_filename}")

    dest_dir = origin_file_path.split("/")[-2]
    logger.info(f"'dest_dir': {dest_dir}")
    if dest_dir not in ["images", "files"]:
        return Response("Directory not allowed", status=403)

    if is_valid_image(uploaded_file):
        allowed_path = os.path.join(current_app.config["MEDIA_FILES_DEST"], "images")
        logger.info(f"'allowed_path': {allowed_path}")
    elif is_valid_file(uploaded_file):
        allowed_path = os.path.join(current_app.config["MEDIA_FILES_DEST"], "files")
        logger.info(f"'allowed_path': {allowed_path}")
    else:
        logger.warning("Invalid file type")
        return False

    logger.info(f"'secured_filename': {secured_filename}")
    logger.info(f"'allowed_path': {allowed_path}")
    result_path = os.path.join(allowed_path, secured_filename)
    logger.info(f"'result_path': {result_path}")
    return result_path


def allowed_path_and_extension(origin_file_path):
    """Checks if a file path is valid and has an allowed extension.

    Performs the following validations:
        *  The file path must be valid according to security and location
        constraints.
           (`is_valid_file_path` check).
        *  The file must have a supported file extension (
        `get_file_extension` check).

    Args:
        origin_file_path (str): The relative file path provided in the request.

    Returns:
        bool: True if the path is valid and the extension is allowed,
        False otherwise.
    """
    logger.info("*** 'allowed_path_and_extension' was triggered ***")
    logger.info(f"'origin_file_path': {origin_file_path}")

    if is_valid_file_path(origin_file_path) and get_file_extension(origin_file_path):
        logger.info("'allowed_path_and_extension' retruns True")
        return True
    return False
