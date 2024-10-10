from storage.storage_strategy import StorageStrategy
from flask import current_app
import os
from extensions.logger import logger


class LocalFileSystemStorage(StorageStrategy):
    def __init__(self, media_files_dest: str) -> None:
        """
        Initializes the storage with a media files destination directory.

        Args:
            media_files_dest (str): Directory where media files are stored.
                                    If not provided, defaults to the config value.
        """
        self.media_files_dest = (
            media_files_dest or current_app.config["MEDIA_FILES_DEST"]
        )

    def save_file(self, file_path: str, file_content: bytes) -> None:
        """
        Saves the file to the local file system.

        Args:
            file_path (str): Path where the file should be saved relative to the media directory.
            file_content (bytes): Content of the file to be saved.
        """
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
                logger.info(f"File saved successfully at: {file_path}")
        except OSError as e:
            logger.error(f"Failed to save file at: {file_path}. Error: {e}")
            raise

    def get_file(self, file_path: str) -> bytes:
        """
        Retrieves the file from the local file system.

        Args:
            file_path (str): Path of the file relative to the media directory.

        Returns:
            bytes: The content of the file.
        """
        full_path = self.make_full_path(file_path)
        logger.info(f"Attempting to retrieve file from: {full_path}")
        try:
            with open(full_path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {full_path}")
            raise
        except OSError as e:
            logger.error(f"Error reading file: {full_path}. Error: {e}")
            raise

    def make_full_path(self, file_path: str) -> str:
        """
        Constructs the full path to the file within the media directory.

        Args:
            file_path (str): Path of the file relative to the media directory.

        Returns:
            str: Full path to the file.
        """
        return os.path.join(self.media_files_dest, file_path)


#
# from storage.storage_strategy import StorageStrategy
# from flask import current_app
# import os
# from extensions.logger import logger
#
#
# class LocalFileSystemStorage(StorageStrategy):
#     def __init__(self, media_files_dest: str = None):
#         """
#         Initializes the storage with a media files destination directory.
#
#         Args:
#             media_files_dest (str): Directory where media files are stored.
#                                     If not provided, defaults to the config value.
#         """
#         self.media_files_dest = media_files_dest or current_app.config["MEDIA_FILES_DEST"]
#
#     def save_file(self, file_path: str, file_content: bytes) -> None:
#         """
#         Saves the file to the local file system.
#
#         Args:
#             file_path (str): Path where the file should be saved relative to the media directory.
#             file_content (bytes): Content of the file to be saved.
#         """
#         full_path = self.make_full_path(file_path)
#         try:
#             with open(full_path, "wb") as f:
#                 f.write(file_content)
#             logger.info(f"File saved successfully at: {full_path}")
#         except OSError as e:
#             logger.error(f"Failed to save file at: {full_path}. Error: {e}")
#             raise
#
#     def get_file(self, file_path: str) -> bytes:
#         """
#         Retrieves the file from the local file system.
#
#         Args:
#             file_path (str): Path of the file relative to the media directory.
#
#         Returns:
#             bytes: The content of the file.
#         """
#         full_path = self.make_full_path(file_path)
#         logger.info(f"Attempting to retrieve file from: {full_path}")
#         try:
#             with open(full_path, "rb") as f:
#                 return f.read()
#         except FileNotFoundError:
#             logger.error(f"File not found: {full_path}")
#             raise
#         except OSError as e:
#             logger.error(f"Error reading file: {full_path}. Error: {e}")
#             raise
#
#     def make_full_path(self, file_path: str) -> str:
#         """
#         Constructs the full path to the file within the media directory.
#
#         Args:
#             file_path (str): Path of the file relative to the media directory.
#
#         Returns:
#             str: Full path to the file.
#         """
#         return os.path.join(self.media_files_dest, file_path)
