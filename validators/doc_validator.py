import os
from interfaces.validation_interface import IFileValidator
from extensions.logger import logger
from config.validation_config import FileValidationConfig, DOCValidationConfig
import re
import io
import olefile
import tempfile
from werkzeug.datastructures.file_storage import FileStorage
from typing import Optional, cast
import traceback


class DOCValidator(IFileValidator):
    def __init__(self) -> None:
        """
        Initializes the ImageValidator with configuration from the validation config.

        The configuration is fetched from the config for the 'DOC' type.
        """
        self.config: DOCValidationConfig = cast(
            DOCValidationConfig, FileValidationConfig.get_config("DOC")
        )

    def is_valid(self, uploaded_file: FileStorage) -> bool:
        logger.info("Validating DOC file")

        file_content = self._get_file_content(uploaded_file)
        if not file_content:
            logger.warning("Failed to read file content")
            return False

        temp_file_path = None
        try:
            temp_file_path = self._create_temp_file(file_content)
            if not temp_file_path:
                logger.warning("Failed to create temporary file")
                return False

            if not self._validate_ole_file(temp_file_path):
                return False

            if not self._validate_file_size(file_content):
                return False

            self._reset_file_stream(uploaded_file, file_content)
            return True
        except Exception as error:
            # Log the error and return None if the file could not be read
            logger.warning(f"Error validating DOC file: {error}")
            return False
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @staticmethod
    def _get_file_content(uploaded_file: FileStorage) -> Optional[bytes]:
        """
        Creates a DOC reader object from the uploaded file.

        Args:
            uploaded_file (FileStorage): The uploaded file object.

        Returns:
            Optional[bytes]: The file content as bytes, or None if the file could not be read.
        """
        try:
            # Read the file content
            return uploaded_file.read()
        except Exception as error:
            # Log the error and return None if the file could not be read
            logger.warning(f"Error reading DOC: {error}")
            return None

    @staticmethod
    def _create_temp_file(file_content: bytes) -> Optional[str]:
        """
        Creates a temporary file from the uploaded file content.

        Args:
            file_content (bytes): The uploaded file content as bytes.

        Returns:
            str: The path to the temporary file.
        """
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                # Write the file content to the temporary file
                temp_file.write(file_content)
                # Flush the buffer to ensure the file is written
                temp_file.flush()
                # Return the path to the temporary file
                return temp_file.name
        except Exception as error:
            # Log the error and return None if the file could not be created
            logger.warning(f"Error creating temporary file: {error}")
            logger.warning(traceback.format_exc())
            return None

    def _validate_ole_file(self, file_path: str) -> bool:
        try:
            with olefile.OleFileIO(file_path) as ole:
                if not self._check_if_word(ole):
                    return False
                if not self._check_macros(ole):
                    return False
                if not self._check_external_links(ole):
                    return False
                if not self._check_embedded_objects(ole):
                    return False

                word_data = self._get_word_document_data(ole)
                if not word_data or not self._validate_word_data(word_data):
                    return False

            return True
        except Exception as error:
            logger.warning(f"Error processing OLE file: {error}")
            logger.warning(traceback.format_exc())
            return False

    @staticmethod
    def _check_if_word(ole: olefile.OleFileIO) -> bool:
        """
        Checks if the uploaded file is a valid Word document.

        Args:
            ole (olefile.OleFileIO): The OleFileIO object.

        Returns:
            bool: True if the file is a valid Word document, False otherwise.
        """
        # Check if it's a Word document
        if not ole.exists("WordDocument"):
            # Log a warning if the file is not a valid Word document
            logger.warning(
                "File is not a valid DOC file (missing 'WordDocument' stream)"
            )
            # Return False to indicate that the file is not valid
            return False
        # Return True to indicate that the file is valid
        return True

    def _check_macros(self, ole: olefile.OleFileIO) -> bool:
        """
        Checks if the uploaded file contains macros.

        Macros can be used to execute malicious code, so we block files that contain them.

        Args:
            ole (olefile.OleFileIO): The OleFileIO object.

        Returns:
            bool: True if the file does not contain macros, False otherwise.
        """
        # Check for macros
        if any(ole.exists(stream) for stream in self.config.macros):
            # Log a warning if the file contains macros
            logger.warning("Document contains macros. Potential security risk.")
            # Return False to indicate that the file contains macros
            return False
        # Return True to indicate that the file does not contain macros
        return True

    @staticmethod
    def _check_external_links(ole: olefile.OleFileIO) -> bool:
        """
        Checks if the uploaded file contains external links.

        External links can be used to execute malicious code, so we block files that contain them.

        Args:
            ole (olefile.OleFileIO): The OleFileIO object.

        Returns:
            bool: True if the file does not contain external links, False otherwise.
        """
        # Check for external links
        if ole.exists("\\1Table"):
            table_data = ole.openstream("\\1Table").read()
            if any(
                protocol in table_data.upper() for protocol in [b"HTTP://", b"HTTPS://"]
            ):
                # Log a warning if the file contains external links
                logger.warning(
                    "Document contains external links. Potential security risk.\
                    This can be used to execute malicious code."
                )
                # Return False to indicate that the file contains external links
                return False
        # Return True to indicate that the file does not contain external links
        return True

    @staticmethod
    def _check_embedded_objects(ole: olefile.OleFileIO) -> bool:
        """
        Checks if the uploaded file contains embedded objects.

        Embedded objects can be used to execute malicious code, so we block files that contain them.

        Args:
            ole (olefile.OleFileIO): The OleFileIO object.

        Returns:
            bool: True if the file does not contain embedded objects, False otherwise.
        """
        # Check for embedded objects.
        # If the file contains an "ObjectPool" stream, it means it has embedded objects,
        # which can be used to execute malicious code. We block such files.
        if ole.exists("ObjectPool"):
            logger.warning(
                "Document contains embedded objects. Potential security risk."
                " This can be used to execute malicious code."
            )
            return False
        # If the file does not contain embedded objects, return True
        return True

    @staticmethod
    def _get_word_document_data(ole: olefile.OleFileIO) -> Optional[bytes]:
        """
        Reads the WordDocument stream from the uploaded file.

        Args:
            ole (olefile.OleFileIO): The OleFileIO object representing the
                uploaded file.

        Returns:
            Optional[bytes]: The data from the WordDocument stream, or None if
                there was an error reading it.
        """
        try:
            # Open the WordDocument stream
            with ole.openstream("WordDocument") as word_stream:
                # Read the data from the stream
                return word_stream.read()
        except Exception as error:
            # Log a warning if there was an error reading the stream
            logger.warning(f"Error reading WordDocument stream: {error}")
            return None

    def _validate_word_data(self, word_data: bytes) -> bool:
        """
        Validates the data from the WordDocument stream.

        This method checks if the uploaded Word document contains potential
        script injection and suspicious keywords.

        Args:
            word_data (bytes): The data from the WordDocument stream.

        Returns:
            bool: True if the file passes all the checks, False otherwise.
        """
        # Check for potential script injection and suspicious keywords
        return all(
            [
                self._check_script_injection(word_data),
                self._check_suspicious_keywords(word_data),
            ]
        )

    @staticmethod
    def _check_script_injection(word_data: bytes) -> bool:
        """
        Checks if the uploaded Word document contains potential script injection.

        This is a security risk, as it could allow an attacker to execute malicious code.
        We check for the strings "<script", "javascript:", and "data:" (ignoring case)
        because these are commonly used to inject malicious code into a Word document.

        Args:
            word_data (bytes): The Word document data as bytes.

        Returns:
            bool: True if the file does not contain script injection, False otherwise.
        """
        # Check Word document for potential script injection
        if re.search(b"(?i)<script|javascript:|data:", word_data, re.IGNORECASE):
            logger.warning("DOC file contains potential script injection")
            return False
        # If the file does not contain script injection, return True
        return True

    def _check_suspicious_keywords(self, word_data: bytes) -> bool:
        """
        Checks if the uploaded Word document contains any suspicious keywords.

        If the file contains any of the configured suspicious keywords, we log a warning
        and return False to indicate that the file is not valid.

        Args:
            word_data (bytes): The Word document data as bytes.

        Returns:
            bool: True if the file does not contain any suspicious keywords, False otherwise.
        """
        # Check if the file contains any suspicious keywords
        if any(
            keyword in word_data.lower() for keyword in self.config.suspicious_keywords
        ):
            # Log a warning if the file contains suspicious keywords
            logger.warning("DOC file contains suspicious keywords")
            # Return False to indicate that the file is not valid
            return False
        # If the file does not contain any suspicious keywords, return True
        return True

    def _validate_file_size(self, file_content: bytes) -> bool:
        """
        Checks if the uploaded file exceeds the maximum allowed file size.

        Args:
            file_content (bytes): The uploaded file content as bytes.

        Returns:
            bool: True if the file size is valid, False if too large.
        """
        # Check if the file size exceeds the maximum allowed
        if len(file_content) > self.config.max_file_size:
            # Log a warning if the file size is suspiciously large
            logger.warning("DOC file is suspiciously large")
            # Return False to indicate that the file is not valid
            return False
        # If the file size is valid, return True
        return True

    @staticmethod
    def _reset_file_stream(uploaded_file: FileStorage, file_content: bytes) -> None:
        """
        Resets the file stream to the beginning and assigns the file content back to the uploaded file.

        This method is used to reset the file stream after it has been read to check its MIME type,
        so it can be read again by the application.

        Args:
            uploaded_file (FileStorage): The uploaded file object.
            file_content (bytes): The file content as bytes.
        """
        # Reset the file stream to the beginning
        file_stream = io.BytesIO(file_content)
        file_stream.seek(0)
        # Assign the file content back to the uploaded file
        uploaded_file.stream = file_stream
