from typing import Union, Tuple
from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.utils import secure_filename

from config.app_config import AppConfig
from extensions.logger import logger
from flask import (
    Response,
    jsonify,
    request,
)
from interfaces.file_handler_interface import IFileHandler
import os

from validators.factory import ValidatorFactory
from storage.storage_strategy import StorageStrategy
from storage.local_storage import LocalFileSystemStorage


class FileRouteHandler(IFileHandler):
    """
    FileRouteHandler manages file handling requests, including retrieving and uploading files.

    Attributes:
        config (dict): Flask app configuration settings.
        storage_strategy (StorageStrategy): Storage strategy for handling file operations.
        validator_factory (ValidatorFactory): Factory for file validators based on file extensions.
    """

    def __init__(
        self,
        config: AppConfig,
        storage_strategy: StorageStrategy = None,
        validator_factory: ValidatorFactory = None,
    ) -> None:
        """
        Initializes the FileRouteHandler with storage and validation strategies.

        Args:
            config (dict): Flask app configuration settings.
            storage_strategy (StorageStrategy, optional): Custom storage strategy. Defaults to LocalFileSystemStorage.
            validator_factory (ValidatorFactory, optional): Custom validator factory. Defaults to ValidatorFactory.
        """
        self.config = config
        self.storage_strategy = storage_strategy or LocalFileSystemStorage(
            media_files_dest=config.MEDIA_FILES_DEST
        )
        self.validator_factory = validator_factory or ValidatorFactory()

    def handle_get_request(
        self, file_path: str
    ) -> Union[Response, Tuple[Response, int]]:
        """
        Handles GET requests to retrieve a file from the media directory.

        Args:
            file_path (str): Relative path to the requested file.

        Returns:
            Union[Response, Tuple[Response, int]]: Flask response object with the file content or an error message.
        """
        logger.info("'GET' method detected")

        try:
            file_content = self.storage_strategy.get_file(file_path)
            return Response(file_content, mimetype="application/octet-stream")
        except FileNotFoundError:
            return jsonify({"error": "File not found"}), 404

    def handle_post_request(
        self, origin_file_path: str
    ) -> Union[Response, Tuple[Response, int]]:
        """
        Handles POST requests for uploading files to the media directory.

        Args:
            origin_file_path (str): The intended path for the uploaded file relative to the media directory.

        Returns:
            Union[Response, Tuple[Response, int]]: Flask response object indicating success or error.
        """
        logger.info("'POST' method detected")

        uploaded_file, file_key = self._get_uploaded_file()
        if uploaded_file is None:
            return jsonify({"error": "No file part or empty filename"}), 400

        file_extension = self._get_file_extension(uploaded_file.filename)
        logger.info(f"File extension: {file_extension}")

        try:
            validator = self.validator_factory.get_validator(file_extension)
            logger.info(f"Validator: {validator}")
            if not validator.is_valid(uploaded_file):
                return jsonify({"error": "Invalid file"}), 400
            # uploaded_file.stream.seek(0)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        try:
            secured_path = self._secure_file_path(origin_file_path, file_key)
            # uploaded_file.stream.seek(0)
            self.storage_strategy.save_file(secured_path, uploaded_file.read())
            # os.chmod(secured_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            os.chmod(secured_path, 0o755)
            return jsonify({"message": "OK"}), 200
        except (ValueError, Exception) as e:
            logger.error(f"Error uploading file: {str(e)}")
            return jsonify({"error": str(e)}), 501

    def _get_uploaded_file(self) -> Tuple[Union[FileStorage, None], str]:
        """
        Retrieves the uploaded file from the request.

        Returns:
            Tuple[Union[FileStorage, None], str]: The uploaded file and its key in request.files or None if no file.
        """
        file_key = "image" if "image" in request.files else "file"
        uploaded_file: FileStorage = request.files[file_key]

        if uploaded_file and uploaded_file.filename:
            return uploaded_file, file_key
        return None, file_key

    def _secure_file_path(self, origin_file_path: str, file_key: str) -> str:
        """
        Secures the file path by verifying the destination and ensuring no unwanted paths.

        Args:
            origin_file_path (str): The file path provided in the request.
            file_key (str): The key used to identify the uploaded file (either "image" or "file").

        Returns:
            str: A secured, sanitized file path to save the file.

        Raises:
            ValueError: If the destination directory is not allowed.
        """
        uploaded_file: FileStorage = request.files[file_key]
        secured_filename = secure_filename(uploaded_file.filename)

        dest_dir = origin_file_path.split("/")[-2]
        if dest_dir not in ["images", "files"]:
            raise ValueError("Directory not allowed")

        allowed_path = os.path.join(self.config.MEDIA_FILES_DEST, dest_dir)
        return os.path.join(allowed_path, secured_filename)

    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """
        Extracts the file extension from the filename.

        Args:
            filename (str): The name of the file.

        Returns:
            str: The file extension in lowercase.
        """
        return filename.rsplit(".", 1)[1].lower()
