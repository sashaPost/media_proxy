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
    file_extension = origin_file_path.split(".")[-1]

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
    parts = req_abs_file_path.split("/")
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
    req_abs_file_path = os.path.abspath(
        os.path.normpath(
            os.path.join(current_app.config["MEDIA_FILES_DEST"], origin_file_path)
        )
    )

    media_abs_path = os.path.abspath(current_app.config["MEDIA_FILES_DEST"])

    allowed_dirs = [
        os.path.join(media_abs_path, directory)
        for directory in current_app.config["ALLOWED_DIRECTORIES"]
    ]

    req_dir = get_request_directory(req_abs_file_path)

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
    uploaded_file = request.files[file_key]

    secured_filename = secure_filename(uploaded_file.filename)

    dest_dir = origin_file_path.split("/")[-2]

    if dest_dir not in ["images", "files"]:
        return Response("Directory not allowed", status=403)

    if is_valid_image(uploaded_file):
        allowed_path = os.path.join(current_app.config["MEDIA_FILES_DEST"], "images")
    elif is_valid_file(uploaded_file):
        allowed_path = os.path.join(current_app.config["MEDIA_FILES_DEST"], "files")
    else:
        logger.warning("Invalid file type")
        return False

    result_path = os.path.join(allowed_path, secured_filename)

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

    if is_valid_file_path(origin_file_path) and get_file_extension(origin_file_path):
        return True
    return False
